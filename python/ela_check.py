import sys
import os
import json
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
#  ela_check.py  —  Error Level Analysis (ELA) forgery detection
#
#  How ELA works:
#    1. Re-save the image at a known JPEG quality level (e.g. 95%)
#    2. Compute pixel-by-pixel difference between original and re-saved
#    3. Amplify the difference map
#    4. Analyse the result:
#       - Authentic image  → uniform, low error across all regions
#       - Edited region    → significantly higher error than background
#         (edited pixels were re-compressed differently from the rest)
#
#  Usage:
#    python ela_check.py <image_path>
#
#  Returns JSON with:
#    checked, ela_score, suspicious, forgery_detected,
#    max_ela, mean_ela, std_ela, high_error_ratio,
#    issues, positives, score_adjustment
# ─────────────────────────────────────────────────────────────────────────────

# Thresholds tuned for scanned/photographed documents
ELA_QUALITY         = 95      # JPEG re-save quality
AMPLIFY_FACTOR      = 15      # Amplification for visualisation (not used in scoring)
HIGH_ERROR_THRESHOLD = 25     # Pixel ELA value above this = suspicious region
FORGERY_RATIO_THRESHOLD = 0.15  # >15% high-error pixels = likely forgery
MEAN_ELA_SUSPICIOUS = 12.0    # Mean ELA above this = suspicious
STD_ELA_SUSPICIOUS  = 18.0    # High std = inconsistent compression = edited


def compute_ela(image_path, quality=ELA_QUALITY):
    """
    Compute Error Level Analysis on an image.
    Returns (ela_array, original_array) or (None, None) on failure.
    """
    try:
        from PIL import Image
        import io

        img = Image.open(image_path).convert('RGB')

        # Re-save at known quality into memory buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        resaved = Image.open(buffer).convert('RGB')

        # Convert to numpy arrays
        orig_arr    = np.array(img,     dtype=np.float32)
        resaved_arr = np.array(resaved, dtype=np.float32)

        # ELA = absolute difference, scaled up for visibility
        ela_arr = np.abs(orig_arr - resaved_arr)
        return ela_arr, orig_arr

    except Exception as e:
        return None, None


def analyse_ela(ela_arr):
    """
    Analyse ELA array and return metrics.
    """
    if ela_arr is None:
        return {}

    # Flatten to single channel (max across RGB)
    ela_max_channel = ela_arr.max(axis=2)

    mean_ela  = float(ela_max_channel.mean())
    std_ela   = float(ela_max_channel.std())
    max_ela   = float(ela_max_channel.max())

    # Ratio of pixels with high error level
    total_pixels     = ela_max_channel.size
    high_error_pixels = int((ela_max_channel > HIGH_ERROR_THRESHOLD).sum())
    high_error_ratio  = high_error_pixels / total_pixels if total_pixels > 0 else 0

    return {
        'mean_ela':         round(mean_ela, 3),
        'std_ela':          round(std_ela, 3),
        'max_ela':          round(max_ela, 3),
        'high_error_pixels': high_error_pixels,
        'high_error_ratio': round(high_error_ratio, 4),
        'total_pixels':     total_pixels,
    }


def check_ela(image_path):
    """
    Main ELA check function.
    Returns dict with forgery detection results.
    """
    issues    = []
    positives = []

    if not os.path.exists(image_path):
        return {
            "checked":          False,
            "ela_score":        70,
            "suspicious":       False,
            "forgery_detected": False,
            "score_adjustment": 0,
            "issues":           ["ELA: File not found"],
            "positives":        [],
            "error":            "File not found"
        }

    # Only works on image files
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'):
        return {
            "checked":          False,
            "ela_score":        70,
            "suspicious":       False,
            "forgery_detected": False,
            "score_adjustment": 0,
            "issues":           [],
            "positives":        ["ELA: Non-image format skipped"]
        }

    try:
        # ── Compute ELA ───────────────────────────────────────────────────────
        ela_arr, orig_arr = compute_ela(image_path)

        if ela_arr is None:
            return {
                "checked":          False,
                "ela_score":        70,
                "suspicious":       False,
                "forgery_detected": False,
                "score_adjustment": 0,
                "issues":           ["ELA computation failed — image may be corrupted"],
                "positives":        []
            }

        metrics = analyse_ela(ela_arr)
        mean_ela        = metrics['mean_ela']
        std_ela         = metrics['std_ela']
        max_ela         = metrics['max_ela']
        high_error_ratio= metrics['high_error_ratio']

        # ── Decision logic ────────────────────────────────────────────────────
        forgery_detected = False
        suspicious       = False
        score_adjustment = 0
        ela_score        = 100

        # Strong forgery signal: high ratio of suspicious pixels AND high mean
        if high_error_ratio > FORGERY_RATIO_THRESHOLD and mean_ela > MEAN_ELA_SUSPICIOUS:
            forgery_detected = True
            suspicious       = True
            score_adjustment = -40
            ela_score        = 20
            issues.append(
                f"⚠ ELA FORGERY DETECTED: {high_error_ratio*100:.1f}% of pixels show "
                f"high error levels (mean ELA: {mean_ela:.1f}) — "
                "image regions were edited after original creation"
            )

        # Medium signal: high std (inconsistent compression = pasted regions)
        elif std_ela > STD_ELA_SUSPICIOUS and mean_ela > 8.0:
            suspicious       = True
            score_adjustment = -20
            ela_score        = 50
            issues.append(
                f"⚠ ELA SUSPICIOUS: Inconsistent compression patterns detected "
                f"(std: {std_ela:.1f}, mean: {mean_ela:.1f}) — "
                "possible copy-paste or text overlay on document"
            )

        # Weak signal: slightly elevated ELA
        elif mean_ela > MEAN_ELA_SUSPICIOUS:
            suspicious       = True
            score_adjustment = -10
            ela_score        = 70
            issues.append(
                f"⚠ ELA WARNING: Elevated error levels detected (mean: {mean_ela:.1f}) — "
                "document may have been processed or lightly edited"
            )

        # Clean document
        else:
            ela_score        = 100
            score_adjustment = 0
            positives.append(
                f"ELA integrity check passed — uniform compression levels "
                f"(mean: {mean_ela:.1f}, ratio: {high_error_ratio*100:.1f}%) — "
                "no pixel-level editing detected"
            )

        return {
            "checked":           True,
            "ela_score":         ela_score,
            "suspicious":        suspicious,
            "forgery_detected":  forgery_detected,
            "mean_ela":          mean_ela,
            "std_ela":           std_ela,
            "max_ela":           max_ela,
            "high_error_ratio":  high_error_ratio,
            "score_adjustment":  score_adjustment,
            "issues":            issues,
            "positives":         positives
        }

    except Exception as e:
        return {
            "checked":          False,
            "ela_score":        70,
            "suspicious":       False,
            "forgery_detected": False,
            "score_adjustment": 0,
            "issues":           [f"ELA check error: {str(e)}"],
            "positives":        []
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "checked": False,
            "error": "Usage: ela_check.py <image_path>"
        }))
        sys.exit(1)

    image_path = sys.argv[1]
    result     = check_ela(image_path)
    print(json.dumps(result, indent=2))