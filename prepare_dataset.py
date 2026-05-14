import os
import shutil
import cv2
from PIL import Image

base = r'C:\xampp\htdocs\doc-verify\dataset'

categories = {
    'diplomas':    'cert',
    'transcripts': 'trans',
    'ids':         'id'
}

real_flat = os.path.join(base, 'real')
counter = 1

print("Preparing and validating dataset...")
print("="*50)

for folder, prefix in categories.items():
    folder_path = os.path.join(base, 'real', folder)
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        continue

    files = [f for f in os.listdir(folder_path)
             if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.webp'))]

    print(f"\n{folder}: {len(files)} images found")

    for fname in files:
        fpath = os.path.join(folder_path, fname)
        try:
            # Validate image can be opened
            img = Image.open(fpath)
            w, h = img.size

            # Resize if too large (max 2000px wide)
            if w > 2000:
                ratio = 2000 / w
                img = img.resize((2000, int(h*ratio)), Image.LANCZOS)

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save with clean name to real/ folder
            new_name = f"{prefix}_{counter:04d}.jpg"
            out_path = os.path.join(real_flat, new_name)
            img.save(out_path, 'JPEG', quality=95)
            counter += 1
            print(f"  OK: {fname} -> {new_name} ({w}x{h})")

        except Exception as e:
            print(f"  ERROR: {fname} - {e}")

print(f"\n{'='*50}")
print(f"Total prepared: {counter-1} images")
print(f"Saved to: {real_flat}")
print("\nNext: run  py python/generate_fakes.py")