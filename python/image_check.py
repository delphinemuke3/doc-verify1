import sys
import json
import cv2
import numpy as np
import os

def check_image(image_path):
    try:
        if not os.path.exists(image_path):
            return {"success": False, "error": "File not found", "score": 0, "issues": [], "positives": []}

        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Could not read image", "score": 0, "issues": [], "positives": []}

        issues = []
        positives = []
        deductions = []

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # --- Resolution check ---
        if w >= 600 and h >= 350:
            positives.append("Good resolution - consistent with a scanned document")
        elif w >= 300 and h >= 200:
            positives.append("Acceptable resolution")
        else:
            issues.append("Very low resolution - possibly a photo of a photo")
            deductions.append(30)

        # --- Sharpness check ---
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        if variance >= 80:
            positives.append("Document is sharp and clear")
        elif variance >= 20:
            positives.append("Acceptable sharpness - may be laminated document")
        elif variance >= 5:
            issues.append("Document appears slightly blurry - could be a photocopy")
            deductions.append(10)
        else:
            issues.append("Document is very blurry - possible tampered or re-photographed")
            deductions.append(25)

        # --- Edge detection ---
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        if edge_density > 0.03:
            positives.append("Clear edge structure detected - consistent with printed document")
        elif edge_density > 0.01:
            pass  # neutral
        else:
            issues.append("Very few edges detected - document may lack printed content")
            deductions.append(15)

        # --- White area check ---
        _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
        white_ratio = np.sum(thresh == 255) / thresh.size
        if white_ratio > 0.92:
            issues.append("Extremely high white area - possible blank or heavily altered document")
            deductions.append(20)
        elif white_ratio > 0.80:
            positives.append("Normal white background ratio for document")

        # --- Color check ---
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat_mean = hsv[:,:,1].mean()
        if sat_mean >= 25:
            positives.append("Color elements detected - consistent with official colored document")
        elif sat_mean >= 10:
            pass  # grayscale - neutral
        else:
            issues.append("No color detected - document is black and white only")
            deductions.append(8)

        # --- Noise check (FIXED: much more lenient thresholds for degree certificates) ---
        noise = np.std(gray.astype(float) - cv2.GaussianBlur(gray, (5,5), 0).astype(float))
        if noise < 5:
            positives.append("Low noise level - consistent with authentic scan")
        elif noise < 15:
            positives.append("Acceptable noise level for scanned document")
        elif noise < 25:
            issues.append("Moderate noise pattern detected - scan quality could be better")
            deductions.append(5)  # reduced from 15 to 5
        else:
            issues.append("High noise pattern detected - scan quality is low")
            deductions.append(12)  # reduced from 15 to 12

        # --- Clone/copy-paste detection ---
        blocks = []
        block_size = 32
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                if block.size == block_size * block_size:
                    blocks.append(block)

        clone_found = False
        if len(blocks) > 20:
            seen = {}
            for block in blocks:
                if np.std(block) < 2:
                    continue
                sample = tuple(block.flatten()[::16].tolist())
                seen.setdefault(sample, 0)
                seen[sample] += 1

            duplicate_groups = [count for count in seen.values() if count > 2]
            if len(duplicate_groups) >= 2:
                clone_found = True

        if clone_found:
            issues.append("Repeated image blocks detected - possible copy-paste manipulation")
            deductions.append(25)
        else:
            positives.append("No cloned regions detected")

        # --- JPEG compression artifact check ---
        if image_path.lower().endswith(('.jpg', '.jpeg')):
            dct_var = np.var(np.float32(gray))
            if dct_var < 100:
                issues.append("Unusual JPEG compression pattern detected")
                deductions.append(10)

        # Calculate score
        total_deduction = sum(deductions)
        score = max(0, min(100, 100 - total_deduction))

        return {
            "success": True,
            "score": score,
            "issues": issues,
            "positives": positives,
            "resolution": f"{w}x{h}",
            "variance": round(float(variance), 2),
            "white_ratio": round(float(white_ratio), 2),
            "saturation": round(float(sat_mean), 2)
        }

    except Exception as e:
        return {"success": False, "error": str(e), "score": 60, "issues": [], "positives": []}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No file path", "score": 0, "issues": [], "positives": []}))
    else:
        result = check_image(sys.argv[1])
        print(json.dumps(result))