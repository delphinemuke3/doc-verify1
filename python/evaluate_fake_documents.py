import os
import json
import csv
import joblib
from train_model import extract_features

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(base_dir, 'python', 'models', 'doc_classifier.pkl')
scaler_path = os.path.join(base_dir, 'python', 'models', 'doc_classifier_scaler.pkl')
output_csv = os.path.join(base_dir, 'python', 'fake_evaluation.csv')
output_json = os.path.join(base_dir, 'python', 'fake_evaluation.json')

if not os.path.exists(model_path) or not os.path.exists(scaler_path):
    print('ERROR: Trained model or scaler not found. Run python/train_model.py first.')
    raise SystemExit(1)

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

fake_dir = os.path.join(base_dir, 'dataset', 'fake')
files = sorted([f for f in os.listdir(fake_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

rows = []
correct = 0
missed = 0

for fname in files:
    path = os.path.join(fake_dir, fname)
    feats = extract_features(path)
    if feats is None:
        print(f'SKIPPING: {fname} (feature extraction failed)')
        continue
    X = scaler.transform([feats])
    predicted = model.predict(X)[0]
    proba = None
    try:
        probs = model.predict_proba(X)[0]
        proba = max(probs) * 100
    except Exception:
        proba = None

    label = 'Fake' if int(predicted) == 0 else 'Real'
    rows.append({
        'filename': fname,
        'predicted': label,
        'probability': f'{proba:.1f}%' if proba is not None else 'N/A'
    })
    if label == 'Fake':
        correct += 1
    else:
        missed += 1

with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['filename', 'predicted', 'probability'])
    writer.writeheader()
    writer.writerows(rows)

summary = {
    'total_fake': len(rows),
    'identified_fake': correct,
    'missed_fake': missed,
    'detection_rate': round((correct / len(rows) * 100) if rows else 0, 2),
}
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print('=' * 60)
print('Fake document evaluation complete')
print(f"Fake documents tested: {summary['total_fake']}")
print(f"Correctly identified fake: {summary['identified_fake']}")
print(f"Missed fake: {summary['missed_fake']}")
print(f"Detection rate: {summary['detection_rate']}%")
print(f'Results saved to: {output_csv} and {output_json}')
