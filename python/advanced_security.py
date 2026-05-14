import sys
import json
import cv2
import numpy as np
import os

def detect_uv_simulation(img_cv):
    """
    Real UV ink glows under UV light - we detect indirect evidence:
    - Unusual color channel separation (UV photos look different)
    - High contrast between certain regions typical of UV-reactive areas
    - Blue channel intensity patterns (UV-reactive inks absorb differently)
    """
    issues    = []
    positives = []
    score     = 100

    hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
    b, g, r = cv2.split(img_cv)

    # UV-reactive inks show strong blue channel response
    blue_dominance = float(b.mean()) / (float(r.mean()) + 1)
    if blue_dominance > 1.1:
        positives.append("Blue channel pattern consistent with official color printing")
        score += 5
    elif blue_dominance < 0.6:
        issues.append("Unusual color channel ratio — may indicate non-official printing")
        score -= 15

    # Check for expected bright regions (where UV ink would glow)
    # Official docs have specific bright emblem areas
    h, w = img_cv.shape[:2]
    top_region    = img_cv[0:h//4, w//4:3*w//4]
    bright_pixels = np.sum(top_region.mean(axis=2) > 220)
    bright_ratio  = bright_pixels / (top_region.shape[0] * top_region.shape[1])

    if bright_ratio > 0.15:
        positives.append("Expected bright emblem/logo region detected in header area")
    elif bright_ratio < 0.05:
        issues.append("Missing expected bright region in document header — logo may be absent")
        score -= 10

    # Check color saturation uniformity (fake docs printed on plain paper
    # have less color depth than security paper)
    sat_std = float(hsv[:,:,1].std())
    if sat_std > 30:
        positives.append("Good color depth variation — consistent with security printing")
    else:
        issues.append("Low color variation — may indicate plain paper printing")
        score -= 10

    score = min(100, max(0, score))
    return {
        "feature":   "uv_simulation",
        "score":     score,
        "issues":    issues,
        "positives": positives
    }

def detect_laser_engraving(img_cv, doc_type='certificate'):
    """
    Laser engraving creates unique pixel intensity patterns:
    - Text has very sharp, consistent edges (not printed blur)
    - Engraved areas show slightly deeper color than surroundings
    - No ink bleeding at edges
    """
    issues    = []
    positives = []
    score     = 100

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # For IDs: laser engraving creates ultra-sharp text edges
    if doc_type == 'national_id':
        # Analyze text sharpness using Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var   = laplacian.var()

        if lap_var > 300:
            positives.append("Very sharp text edges detected — consistent with laser engraving")
            score += 5
        elif lap_var > 100:
            positives.append("Good sharpness — acceptable for official document")
        else:
            issues.append("Blurry text edges — laser-engraved IDs should have very sharp text")
            score -= 20

        # Check for consistent ink depth (laser engraving is very uniform)
        # Sample text regions and check intensity uniformity
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text_pixels = gray[binary == 0]
        if len(text_pixels) > 100:
            text_std = float(text_pixels.std())
            if text_std < 25:
                positives.append("Uniform text intensity — consistent with laser engraving")
            else:
                issues.append("Uneven text intensity — may indicate inkjet or toner printing")
                score -= 15
    else:
        # For certificates: check print quality consistency
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var   = laplacian.var()
        if lap_var > 50:
            positives.append("Print quality consistent with official document production")
        else:
            issues.append("Poor print quality detected")
            score -= 10

    score = min(100, max(0, score))
    return {
        "feature":   "laser_engraving",
        "score":     score,
        "issues":    issues,
        "positives": positives
    }

def detect_hologram(img_cv, doc_type='certificate'):
    """
    Hologram stickers appear as:
    - Iridescent/rainbow color patches in specific locations
    - High local color variance in a small circular/oval region
    - Specific locations: bottom center for RP certs, top right for IDs
    """
    issues    = []
    positives = []
    score     = 100
    h, w      = img_cv.shape[:2]

    def check_region_for_hologram(region, name):
        if region.size == 0:
            return False, f"Could not analyze {name} region"
        hsv    = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        hue_std = float(hsv[:,:,0].std())
        sat_mean= float(hsv[:,:,1].mean())
        # Holograms have high hue variation and good saturation
        if hue_std > 40 and sat_mean > 60:
            return True, f"Hologram-like iridescent pattern detected in {name}"
        elif hue_std > 20:
            return None, f"Possible hologram in {name} — hue variation present"
        else:
            return False, f"No hologram detected in {name}"

    if doc_type == 'certificate':
        # RP certificates: hologram/seal at bottom center
        bot_region = img_cv[int(h*0.75):int(h*0.95),
                            int(w*0.35):int(w*0.65)]
        found, msg = check_region_for_hologram(bot_region, "bottom center")
        if found is True:
            positives.append(msg)
            score += 5
        elif found is None:
            positives.append(msg)
        else:
            # Check for RP seal (circular stamp) as alternative
            gray = cv2.cvtColor(bot_region, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 50,
                param1=50, param2=30, minRadius=30, maxRadius=150
            )
            if circles is not None:
                positives.append("Official circular seal/stamp detected in expected location")
                score += 5
            else:
                issues.append("No official seal or hologram detected in expected location")
                score -= 15

    elif doc_type == 'national_id':
        # Rwandan IDs: hologram typically top right or center
        tr_region = img_cv[int(h*0.05):int(h*0.40),
                           int(w*0.60):int(w*0.95)]
        found, msg = check_region_for_hologram(tr_region, "top right")
        if found is True:
            positives.append(msg)
            score += 5
        elif found is False:
            issues.append("No hologram detected in expected ID position")
            score -= 10
        else:
            positives.append(msg)

    score = min(100, max(0, score))
    return {
        "feature":   "hologram",
        "score":     score,
        "issues":    issues,
        "positives": positives
    }

def detect_microtext(img_cv):
    """
    Microtext detection: very small text patterns in borders/backgrounds.
    Real documents have readable microtext; fakes have blurry blobs.
    """
    issues    = []
    positives = []
    score     = 100

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Check border regions for microtext (fine detail patterns)
    border_regions = [
        gray[0:50, :],           # top border
        gray[h-50:h, :],         # bottom border
        gray[:, 0:50],           # left border
        gray[:, w-50:w],         # right border
    ]

    fine_detail_scores = []
    for region in border_regions:
        if region.size == 0:
            continue
        lap = cv2.Laplacian(region, cv2.CV_64F)
        fine_detail_scores.append(lap.var())

    avg_detail = float(np.mean(fine_detail_scores)) if fine_detail_scores else 0

    if avg_detail > 200:
        positives.append("Fine detail pattern detected in borders — consistent with microtext/guilloche")
        score += 5
    elif avg_detail > 50:
        positives.append("Border pattern detected")
    else:
        issues.append("No fine detail in border areas — microtext/guilloche pattern may be missing")
        score -= 10

    score = min(100, max(0, score))
    return {
        "feature":   "microtext",
        "score":     score,
        "issues":    issues,
        "positives": positives
    }

def run_advanced_checks(image_path, doc_type='certificate'):
    try:
        if not os.path.exists(image_path):
            return {"success": False, "error": "File not found"}

        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Cannot read image"}

        # Run all advanced checks
        uv     = detect_uv_simulation(img)
        laser  = detect_laser_engraving(img, doc_type)
        holo   = detect_hologram(img, doc_type)
        micro  = detect_microtext(img)

        # Combined advanced score
        adv_score = round(
            (uv['score']    * 0.20) +
            (laser['score'] * 0.35) +
            (holo['score']  * 0.25) +
            (micro['score'] * 0.20)
        )

        all_issues    = (uv['issues']    + laser['issues'] +
                         holo['issues']  + micro['issues'])
        all_positives = (uv['positives'] + laser['positives'] +
                         holo['positives'] + micro['positives'])

        return {
            "success":          True,
            "advanced_score":   adv_score,
            "uv_score":         uv['score'],
            "laser_score":      laser['score'],
            "hologram_score":   holo['score'],
            "microtext_score":  micro['score'],
            "issues":           all_issues,
            "positives":        all_positives
        }

    except Exception as e:
        return {
            "success":        False,
            "error":          str(e),
            "advanced_score": 60,
            "issues":         [],
            "positives":      []
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No file path"}))
    else:
        image_path = sys.argv[1]
        doc_type   = sys.argv[2] if len(sys.argv) > 2 else 'certificate'
        print(json.dumps(run_advanced_checks(image_path, doc_type)))