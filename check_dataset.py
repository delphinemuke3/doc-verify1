import os
import cv2
import numpy as np
from PIL import Image

base  = r'C:\xampp\htdocs\doc-verify\dataset'
real  = os.path.join(base, 'real')
fake  = os.path.join(base, 'fake')

def count_and_check(folder, label):
    files = [f for f in os.listdir(folder)
             if f.lower().endswith(('.jpg','.jpeg','.png'))]
    print(f"\n{label}: {len(files)} images")
    sizes = []
    corrupt = []
    for f in files:
        try:
            img = Image.open(os.path.join(folder, f))
            sizes.append(img.size)
        except:
            corrupt.append(f)

    if sizes:
        widths  = [s[0] for s in sizes]
        heights = [s[1] for s in sizes]
        print(f"  Avg size: {int(np.mean(widths))}x{int(np.mean(heights))} px")
        print(f"  Min size: {min(widths)}x{min(heights)} px")
        print(f"  Max size: {max(widths)}x{max(heights)} px")

    if corrupt:
        print(f"  CORRUPT files: {corrupt}")
    else:
        print(f"  All images valid")

    return len(files)

print("="*50)
print("DATASET SUMMARY")
print("="*50)

real_count = count_and_check(real, "REAL documents")
fake_count = count_and_check(fake, "FAKE documents")
total      = real_count + fake_count

print(f"\n{'='*50}")
print(f"Total samples:  {total}")
print(f"Real:           {real_count} ({real_count/total*100:.1f}%)")
print(f"Fake:           {fake_count} ({fake_count/total*100:.1f}%)")

if real_count < 10:
    print("\nWARNING: Need at least 10 real documents to train")
elif real_count < 20:
    print("\nOK: Dataset is small but trainable")
    print("Recommendation: collect more real documents for better accuracy")
else:
    print("\nGREAT: Dataset size is good for training!")

print("\nNext step: py python/train_model.py")