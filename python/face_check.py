import sys
import json
import cv2
import numpy as np
import os

def detect_face(image_path):
    try:
        if not os.path.exists(image_path):
            return {"success": False, "error": "File not found",
                    "face_found": False, "face_count": 0, "issues": [], "positives": []}

        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Cannot read image",
                    "face_found": False, "face_count": 0, "issues": [], "positives": []}

        issues = []
        positives = []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Load OpenCV face cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)

        # Also load profile face cascade for tilted photos
        profile_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
        profile_cascade = cv2.CascadeClassifier(profile_path)

        # Detect frontal faces with multiple scale factors
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=3,
            minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
        )

        face_count = len(faces)

        # Try profile detection if no frontal face found
        if face_count == 0:
            profiles = profile_cascade.detectMultiScale(
                gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30)
            )
            face_count = len(profiles)
            if face_count > 0:
                positives.append("Face detected (profile view) — consistent with ID photo")

        if face_count == 1:
            positives.append("Exactly one face detected — consistent with ID document")
            # Check face is in expected region (left or right portion of ID)
            h, w = img.shape[:2]
            face = faces[0] if len(faces) > 0 else None
            if face is not None:
                fx, fy, fw, fh = face
                face_center_x = fx + fw // 2
                # Face should be in left 40% or right 40% of document
                if face_center_x < w * 0.5:
                    positives.append("Face positioned in expected ID photo area")
                else:
                    positives.append("Face detected on document")

            # Check face size is reasonable (not too small)
            if face is not None:
                fx, fy, fw, fh = face
                face_area_ratio = (fw * fh) / (img.shape[0] * img.shape[1])
                if face_area_ratio > 0.02:
                    positives.append("Face photo size is appropriate for ID document")
                else:
                    issues.append("Detected face is very small — may not be a proper ID photo")

        elif face_count == 0:
            issues.append("No face detected — ID document should have a photo")
        elif face_count > 1:
            issues.append(f"{face_count} faces detected — ID should have only one photo")

        # Check photo region quality
        if face_count > 0 and len(faces) > 0:
            fx, fy, fw, fh = faces[0]
            face_region = gray[fy:fy+fh, fx:fx+fw]
            if face_region.size > 0:
                face_contrast = np.std(face_region)
                if face_contrast < 15:
                    issues.append("Face photo area has very low contrast — may be tampered")
                elif face_contrast > 20:
                    positives.append("Face photo has good contrast and clarity")

        face_found = face_count > 0

        return {
            "success": True,
            "face_found": face_found,
            "face_count": face_count,
            "issues": issues,
            "positives": positives,
            "score": 100 if face_count == 1 else (70 if face_count > 1 else 40)
        }

    except Exception as e:
        return {
            "success": False, "error": str(e),
            "face_found": False, "face_count": 0,
            "issues": [], "positives": [], "score": 60
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No file path"}))
    else:
        print(json.dumps(detect_face(sys.argv[1])))