import os
import json
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample
import joblib
import re

pytesseract.pytesseract.tesseract_cmd = \
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'

RWANDA_KEYWORDS = [
    'REPUBLIC OF RWANDA', 'RWANDA POLYTECHNIC', 'UNIVERSITY OF RWANDA',
    'INDANGAMUNTU', 'NIDA', 'NATIONAL ID', 'CERTIFICATE', 'DIPLOMA',
    'DEGREE', 'TRANSCRIPT', 'IPRC', 'RP', 'UR', 'WDA', 'REB',
    'KIGALI', 'RWANDA', 'VICE CHANCELLOR', 'RECTOR', 'REGISTRAR',
    'THIS IS TO CERTIFY', 'ADVANCED DIPLOMA', 'CONGREGATION',
    'POLYTECHNIC', 'POLYTEC'
]

AUTH_KEYWORDS = [
    'VICE CHANCELLOR', 'RECTOR', 'REGISTRAR',
    'PRINCIPAL', 'DIRECTOR', 'CHANCELLOR',
    'CHARGE OF ACADEMICS', 'INSTITUTIONAL ADVANCEMENT'
]

def extract_features(image_path):
    try:
        img_cv  = cv2.imread(image_path)
        img_pil = Image.open(image_path)

        if img_cv is None:
            return None

        h, w  = img_cv.shape[:2]
        gray  = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        feats = []

        # 1. Resolution score
        feats.append(min(100, (w * h) / (800 * 600) * 100))

        # 2. Sharpness
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        feats.append(min(100, lap_var / 5))

        # 3. Edge density
        edges = cv2.Canny(gray, 50, 150)
        feats.append((np.sum(edges > 0) / edges.size) * 100)

        # 4. White area ratio
        _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
        feats.append((np.sum(thresh == 255) / thresh.size) * 100)

        # 5. Color saturation
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        feats.append(hsv[:, :, 1].mean())

        # 6. Texture richness
        local_stds = []
        block = 16
        for y in range(0, h - block, block):
            for x in range(0, w - block, block):
                local_stds.append(np.std(gray[y:y+block, x:x+block]))
        feats.append(np.mean(local_stds) if local_stds else 0)

        # 7. Noise level
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        feats.append(np.std(gray.astype(float) - blurred.astype(float)))

        # 8. Clone score
        blocks_list = []
        bs = 48
        for y in range(0, h - bs, bs):
            for x in range(0, w - bs, bs):
                b = gray[y:y+bs, x:x+bs]
                blocks_list.append(tuple(b[::6, ::6].flatten().tolist()))
        seen = {}
        clone_count = 0
        for i, b in enumerate(blocks_list):
            if b in seen:
                clone_count += 1
            seen[b] = i
        feats.append(min(100, clone_count * 10))

        # 9. OCR word count
        try:
            img_enh = ImageEnhance.Contrast(
                img_pil.convert('L')
            ).enhance(2.0)
            text = pytesseract.image_to_string(
                img_enh, config='--oem 3 --psm 6'
            )
            word_count = len(text.split())
        except:
            text = ''
            word_count = 0
        feats.append(min(100, word_count))

        # 10. Rwanda keyword count
        text_upper = text.upper() if text else ''
        feats.append(sum(1 for kw in RWANDA_KEYWORDS if kw in text_upper))

        # 11. Authority keyword present
        feats.append(int(any(kw in text_upper for kw in AUTH_KEYWORDS)))

        # 12. Date pattern present
        feats.append(int(bool(re.findall(
            r'\d{2}[./\-]\d{2}[./\-]\d{4}|\d{4}[./\-]\d{2}[./\-]\d{2}',
            text
        ))))

        # 13. ID number pattern
        feats.append(int(bool(re.findall(r'\b\d{16}\b|\b\d{10}\b', text))))

        # 14. Face detected
        fc = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = fc.detectMultiScale(
            gray, scaleFactor=1.05,
            minNeighbors=3, minSize=(30, 30)
        )
        feats.append(int(len(faces) > 0))

        # 15. QR code present
        qr_data, _, _ = cv2.QRCodeDetector().detectAndDecode(img_cv)
        feats.append(int(bool(qr_data)))

        return feats

    except Exception as e:
        print(f"  Feature error on {os.path.basename(image_path)}: {e}")
        return None


def load_dataset(real_dir, fake_dir):
    X_real, X_fake = [], []

    print(f"\nLoading REAL documents from: {real_dir}")
    for fname in sorted(os.listdir(real_dir)):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            fpath = os.path.join(real_dir, fname)
            feats = extract_features(fpath)
            if feats:
                X_real.append(feats)
                print(f"  [REAL] {fname}")

    print(f"\nLoading FAKE documents from: {fake_dir}")
    loaded = 0
    for fname in sorted(os.listdir(fake_dir)):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            fpath = os.path.join(fake_dir, fname)
            feats = extract_features(fpath)
            if feats:
                X_fake.append(feats)
                loaded += 1
                if loaded % 10 == 0:
                    print(f"  [FAKE {loaded:03d}] {fname}")

    print(f"\nLoaded: {len(X_real)} real, {len(X_fake)} fake")
    return np.array(X_real), np.array(X_fake)


def balance_dataset(X_real, X_fake):
    """Balance dataset so real and fake are equal."""
    print("\nBalancing dataset...")

    # Oversample real documents to match fake count
    # This means duplicating real samples with slight variation
    target = len(X_fake)

    if len(X_real) < target:
        # Oversample real with replacement
        X_real_balanced = resample(
            X_real,
            replace=True,
            n_samples=target,
            random_state=42
        )
        print(f"  Oversampled real: {len(X_real)} -> {len(X_real_balanced)}")
    else:
        X_real_balanced = X_real

    # Combine
    X = np.vstack([X_real_balanced, X_fake])
    y = np.array([1]*len(X_real_balanced) + [0]*len(X_fake))

    print(f"  Final dataset: {len(X_real_balanced)} real + "
          f"{len(X_fake)} fake = {len(X)} total")
    return X, y


def train():
    base         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    real_dir     = os.path.join(base, 'dataset', 'real')
    fake_dir     = os.path.join(base, 'dataset', 'fake')
    models_dir   = os.path.join(base, 'python', 'models')
    model_path   = os.path.join(models_dir, 'doc_classifier.pkl')
    scaler_path  = os.path.join(models_dir, 'doc_classifier_scaler.pkl')
    metrics_path = os.path.join(models_dir, 'doc_classifier_metrics.json')

    os.makedirs(models_dir, exist_ok=True)

    print("="*60)
    print("  AI Document Classifier — Training (Balanced)")
    print("="*60)

    X_real, X_fake = load_dataset(real_dir, fake_dir)

    if len(X_real) == 0 or len(X_fake) == 0:
        print("ERROR: Need both real and fake samples.")
        return

    # Balance dataset
    X, y = balance_dataset(X_real, X_fake)

    # Scale features
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"\nTraining set : {len(X_train)} samples")
    print(f"Testing set  : {len(X_test)} samples")
    print(f"Real in test : {np.sum(y_test==1)}")
    print(f"Fake in test : {np.sum(y_test==0)}")
    print("\nTraining Random Forest classifier...")

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        class_weight='balanced'
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    cm     = confusion_matrix(y_test, y_pred)

    print("\n" + "="*60)
    print("  MODEL EVALUATION RESULTS")
    print("="*60)
    print(f"\n  Overall Accuracy : {acc*100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=['Fake', 'Real'],
        zero_division=0
    ))

    print("Confusion Matrix:")
    print(f"  True Fake  (correctly identified fake): {cm[0][0]}")
    print(f"  False Real (fake missed as real):       {cm[0][1]}")
    print(f"  False Fake (real wrongly flagged):      {cm[1][0]}")
    print(f"  True Real  (correctly identified real): {cm[1][1]}")

    # Fake detection rate
    fake_detection_rate = cm[0][0] / (cm[0][0] + cm[0][1]) * 100 \
        if (cm[0][0] + cm[0][1]) > 0 else 0
    real_detection_rate = cm[1][1] / (cm[1][0] + cm[1][1]) * 100 \
        if (cm[1][0] + cm[1][1]) > 0 else 0

    print(f"\n  Fake detection rate : {fake_detection_rate:.2f}%")
    print(f"  Real detection rate : {real_detection_rate:.2f}%")

    # Cross validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X_scaled, y, cv=skf)
    print(f"\nCross-validation (5-fold):")
    print(f"  Scores     : {[f'{s*100:.1f}%' for s in cv_scores]}")
    print(f"  Mean       : {cv_scores.mean()*100:.2f}%")
    print(f"  Std dev    : {cv_scores.std()*100:.2f}%")

    # Feature importance
    feat_names = [
        'resolution','sharpness','edge_density','white_ratio',
        'saturation','texture','noise','clone_score','word_count',
        'rwanda_keywords','authority_found','date_found',
        'id_number_found','face_found','qr_found'
    ]
    importances = clf.feature_importances_
    sorted_idx  = np.argsort(importances)[::-1]

    print("\nFeature importances:")
    for i in sorted_idx:
        bar = '█' * int(importances[i] * 100)
        print(f"  {feat_names[i]:20s}: {importances[i]*100:5.2f}%  {bar}")

    # Save
    joblib.dump(clf,    model_path)
    joblib.dump(scaler, scaler_path)

    metrics = {
        "accuracy":             round(acc * 100, 2),
        "fake_detection_rate":  round(fake_detection_rate, 2),
        "real_detection_rate":  round(real_detection_rate, 2),
        "cv_mean":              round(cv_scores.mean() * 100, 2),
        "cv_std":               round(cv_scores.std() * 100, 2),
        "cv_scores":            [round(s*100,2) for s in cv_scores],
        "total_samples":        len(X),
        "real_samples":         int(np.sum(y == 1)),
        "fake_samples":         int(np.sum(y == 0)),
        "true_fake":            int(cm[0][0]),
        "false_real":           int(cm[0][1]),
        "false_fake":           int(cm[1][0]),
        "true_real":            int(cm[1][1]),
        "feature_names":        feat_names,
        "feature_importance":   {
            feat_names[i]: round(float(importances[i]) * 100, 2)
            for i in sorted_idx
        }
    }
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Model saved   : {model_path}")
    print(f"  Scaler saved  : {scaler_path}")
    print(f"  Metrics saved : {metrics_path}")
    print(f"{'='*60}")
    print("\nTraining complete! Model is ready to use.")

if __name__ == "__main__":
    train()