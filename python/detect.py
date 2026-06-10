import sys
import json
import os
import cv2
import numpy as np
from ultralytics import YOLO

# Path to trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'best.pt')

# ── Per-class minimum confidence thresholds ───────────────────────────────────
# Lower threshold for documents that are harder to photograph clearly
CLASS_MIN_CONFIDENCE = {
    "Rwanda Driving License": 30.0,
    "Rwanda National ID":     40.0,
    "NESA Certificate":       40.0,
    "RP Degree":              40.0,
    "RP Transcript":          40.0,
    "ULK Degree":             40.0,
    "ULK Transcript":         40.0,
    "UR Degree":              40.0,
    "UR Transcript":          40.0,
    "MKU Transcript":         40.0,
    "UTAB Degree":            40.0,
    "MKU Degree":             40.0,
    "UTAB Transcript":        40.0,
}
DEFAULT_MIN_CONFIDENCE = 25.0
CLASS_INFO = {
    "MKU Degree": {
        "color": (180, 50, 50),
        "type": "degree",
        "description": "Mount Kenya University Degree Certificate"
    },
    "MKU Transcript": {
        "color": (200, 80, 80),
        "type": "transcript",
        "description": "Mount Kenya University Academic Transcript"
    },
    "NESA Certificate": {
        "color": (34, 139, 34),
        "type": "certificate",
        "description": "National Examination and School Inspection Certificate"
    },
    "RP Degree": {
        "color": (128, 0, 128),
        "type": "degree",
        "description": "Rwanda Polytechnic Degree Certificate"
    },
    "RP Transcript": {
        "color": (153, 50, 204),
        "type": "transcript",
        "description": "Rwanda Polytechnic Academic Transcript"
    },
    "Rwanda Driving License": {
        "color": (210, 105, 30),
        "type": "license",
        "description": "Rwanda Driving License"
    },
    "Rwanda National ID": {
        "color": (24, 95, 165),
        "type": "id",
        "description": "Rwanda National Identification Card"
    },
    "ULK Degree": {
        "color": (0, 100, 0),
        "type": "degree",
        "description": "Universite Libre de Kigali Degree Certificate"
    },
    "ULK Transcript": {
        "color": (59, 109, 17),
        "type": "transcript",
        "description": "Universite Libre de Kigali Academic Transcript"
    },
    "UR Degree": {
        "color": (184, 134, 11),
        "type": "degree",
        "description": "University of Rwanda Degree Certificate"
    },
    "UR Transcript": {
        "color": (186, 117, 23),
        "type": "transcript",
        "description": "University of Rwanda Academic Transcript"
    },
    "UTAB Degree": {
        "color": (70, 130, 180),
        "type": "degree",
        "description": "University of Technology and Arts of Byumba Degree Certificate"
    },
    "UTAB Transcript": {
        "color": (100, 149, 237),
        "type": "transcript",
        "description": "University of Technology and Arts of Byumba Academic Transcript"
    },
}


def run_detection(image_path, confidence=0.10):
    try:
        if not os.path.exists(image_path):
            return {
                "success":    False,
                "error":      f"Image file not found: {image_path}",
                "detections": [],
                "verified":   False,
                "score":      0
            }

        if not os.path.exists(MODEL_PATH):
            return {
                "success":    False,
                "error":      f"Model not found at: {MODEL_PATH}.",
                "detections": [],
                "verified":   False,
                "score":      0
            }

        model   = YOLO(MODEL_PATH)
        img_bgr = cv2.imread(image_path)

        if img_bgr is None:
            return {
                "success":    False,
                "error":      "Could not read image file. Make sure it is a valid JPG or PNG.",
                "detections": [],
                "verified":   False,
                "score":      0
            }

        # Run at low raw confidence — we apply per-class thresholds ourselves
        results = model(img_bgr, conf=confidence, verbose=False)[0]

        detections   = []
        highest_conf = 0

        for box in results.boxes:
            cls_name = model.names[int(box.cls)]
            conf_val = float(box.conf)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            info  = CLASS_INFO.get(cls_name, {})
            color = info.get("color", (100, 100, 100))

            # Draw bounding box
            cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 3)

            # Draw label background
            label = f"{cls_name}  {conf_val:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            cv2.rectangle(img_bgr, (x1, y1 - th - 12), (x1 + tw + 10, y1), color, -1)
            cv2.putText(img_bgr, label, (x1 + 5, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            if conf_val > highest_conf:
                highest_conf = conf_val

            detections.append({
                "class":       cls_name,
                "type":        info.get("type", "unknown"),
                "description": info.get("description", cls_name),
                "confidence":  round(conf_val * 100, 1),
                "bbox":        [x1, y1, x2, y2]
            })

        # Save annotated image
        base, ext   = os.path.splitext(image_path)
        output_path = base + "_detected" + ext
        cv2.imwrite(output_path, img_bgr)

        # ── Apply per-class confidence threshold ──────────────────────────────
        model_confidence = round(highest_conf * 100, 1) if detections else 0
        top_class        = detections[0]['class'] if detections else ''
        min_conf         = CLASS_MIN_CONFIDENCE.get(top_class, DEFAULT_MIN_CONFIDENCE)
        verified         = len(detections) > 0 and model_confidence >= min_conf
        score            = 100 if verified else 0

        # Build result
        result = {
            "success":           True,
            "verified":          verified,
            "score":             score,
            "model_confidence":  model_confidence,
            "detections":        detections,
            "output_image":      output_path,
            "total_found":       len(detections),
            "min_conf_used":     min_conf,
        }

        # Add helpful message if detected but below threshold
        if detections and not verified:
            doc_type = top_class
            if doc_type in ("Rwanda Driving License", "Rwanda National ID"):
                result["low_conf_hint"] = (
                    f"Document detected as {doc_type} at {model_confidence}% confidence "
                    f"(minimum required: {min_conf}%). "
                    "Please upload a clear, flat, well-lit scan of the front of the document."
                )
            else:
                result["low_conf_hint"] = (
                    f"Document detected at {model_confidence}% confidence "
                    f"(minimum required: {min_conf}%). "
                    "Please upload a higher quality image."
                )

        return result

    except Exception as e:
        return {
            "success":    False,
            "error":      str(e),
            "detections": [],
            "verified":   False,
            "score":      0
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error":   "Usage: detect.py <image_path> [confidence 0-100]"
        }))
        sys.exit(1)

    image_path = sys.argv[1]
    confidence = 0.10  # default low — per-class thresholds applied internally
    if len(sys.argv) > 2:
        raw_confidence = float(sys.argv[2])
        confidence = raw_confidence / 100 if raw_confidence > 1 else raw_confidence

    result = run_detection(image_path, confidence)
    print(json.dumps(result))
