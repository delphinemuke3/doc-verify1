import cv2
import numpy as np
import os
import random

def add_tampering(img_cv, method='text_edit'):
    img = img_cv.copy()
    h, w = img.shape[:2]

    if method == 'text_edit':
        x1 = random.randint(w//4, w//2)
        y1 = random.randint(h//4, h//2)
        x2 = x1 + random.randint(60, 150)
        y2 = y1 + random.randint(15, 30)
        cv2.rectangle(img, (x1,y1), (x2,y2), (255,255,255), -1)
        cv2.putText(img, 'ALTERED', (x1+2, y1+18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)

    elif method == 'clone':
        sx = random.randint(0, w//2)
        sy = random.randint(0, h//2)
        sw = random.randint(50, 120)
        sh = random.randint(30, 80)
        if sx+sw < w and sy+sh < h:
            region = img[sy:sy+sh, sx:sx+sw].copy()
            dx = min(random.randint(w//2, w-sw-1), w-sw-1)
            dy = min(random.randint(h//2, h-sh-1), h-sh-1)
            img[dy:dy+sh, dx:dx+sw] = region

    elif method == 'blur':
        x1 = random.randint(0, w//3)
        y1 = random.randint(0, h//3)
        x2 = min(x1 + random.randint(100, w//2), w)
        y2 = min(y1 + random.randint(80, h//2), h)
        region = img[y1:y2, x1:x2]
        if region.size > 0:
            img[y1:y2, x1:x2] = cv2.GaussianBlur(region, (21,21), 0)

    elif method == 'noise':
        noise = np.random.randint(0, 80, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)

    elif method == 'resize_quality':
        scale = random.uniform(0.2, 0.4)
        small = cv2.resize(img, (int(w*scale), int(h*scale)))
        img = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    elif method == 'color_shift':
        shift = np.full(img.shape, (60, 0, 0), dtype=np.uint8)
        img = cv2.add(img, shift)

    elif method == 'whiteout':
        for _ in range(random.randint(2, 5)):
            x1 = random.randint(0, w-80)
            y1 = random.randint(0, h-20)
            cv2.rectangle(img,
                (x1, y1),
                (x1+random.randint(40,80), y1+random.randint(10,20)),
                (255,255,255), -1)

    return img

def generate_fakes(real_dir, fake_dir, multiplier=5):
    os.makedirs(fake_dir, exist_ok=True)
    methods = ['text_edit','clone','blur','noise',
               'resize_quality','color_shift','whiteout']
    generated = 0

    real_files = [f for f in os.listdir(real_dir)
                  if f.lower().endswith(('.jpg','.jpeg','.png'))]

    if not real_files:
        print("No real documents found in:", real_dir)
        return

    print(f"Found {len(real_files)} real documents.")
    print(f"Generating {len(real_files)*multiplier} fake documents...")
    print("="*50)

    for fname in real_files:
        fpath = os.path.join(real_dir, fname)
        img   = cv2.imread(fpath)
        if img is None:
            print(f"  SKIP: {fname} (cannot read)")
            continue

        for i in range(multiplier):
            method   = methods[i % len(methods)]
            fake_img = add_tampering(img.copy(), method)
            base     = os.path.splitext(fname)[0]
            out_name = f"fake_{base}_{method}_{i}.jpg"
            out_path = os.path.join(fake_dir, out_name)
            cv2.imwrite(out_path, fake_img,
                        [cv2.IMWRITE_JPEG_QUALITY, 85])
            generated += 1
            print(f"  Generated: {out_name}")

    print(f"\n{'='*50}")
    print(f"Done! Generated {generated} fake documents.")
    print(f"Saved to: {fake_dir}")
    print(f"\nNext step: py python/train_model.py")

if __name__ == "__main__":
    base     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    real_dir = os.path.join(base, 'dataset', 'real')
    fake_dir = os.path.join(base, 'dataset', 'fake')
    generate_fakes(real_dir, fake_dir, multiplier=5)