import os
import cv2
import shutil
import urllib.request
import zipfile

print("Downloading MIDV-500 dataset...")

base = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(base, 'dataset', 'midv500')
real_dir    = os.path.join(base, 'dataset', 'real_midv')
os.makedirs(dataset_dir, exist_ok=True)
os.makedirs(real_dir, exist_ok=True)

# MIDV-500 direct download links (individual zips per document type)
MIDV_URLS = [
    "http://smartengines.com/midv-500/dataset/01_alb_id.zip",
    "http://smartengines.com/midv-500/dataset/02_aut_drvlic.zip",
    "http://smartengines.com/midv-500/dataset/03_aut_id.zip",
    "http://smartengines.com/midv-500/dataset/04_aut_passport.zip",
    "http://smartengines.com/midv-500/dataset/05_bel_passport.zip",
    "http://smartengines.com/midv-500/dataset/06_bra_drvlic.zip",
    "http://smartengines.com/midv-500/dataset/07_can_drvlic.zip",
    "http://smartengines.com/midv-500/dataset/08_cze_id.zip",
    "http://smartengines.com/midv-500/dataset/09_cze_passport.zip",
    "http://smartengines.com/midv-500/dataset/10_deu_id.zip",
]

def show_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 / total_size)
        print(f"\r  Progress: {pct:.1f}% ({downloaded//1024}KB / {total_size//1024}KB)", end='')

extracted_total = 0

for url in MIDV_URLS:
    fname    = url.split('/')[-1]
    zip_path = os.path.join(dataset_dir, fname)

    if not os.path.exists(zip_path):
        print(f"\nDownloading {fname}...")
        try:
            urllib.request.urlretrieve(url, zip_path, show_progress)
            print(f"\n  Downloaded: {fname}")
        except Exception as e:
            print(f"\n  Failed: {e}")
            continue
    else:
        print(f"\nAlready downloaded: {fname}")

    # Extract zip
    try:
        extract_dir = os.path.join(dataset_dir, fname.replace('.zip',''))
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        print(f"  Extracted to: {extract_dir}")
    except Exception as e:
        print(f"  Extract error: {e}")
        continue

    # Copy/extract frames to real_midv
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            fpath = os.path.join(root, f)
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                out = os.path.join(real_dir, f"midv_{extracted_total:04d}.jpg")
                shutil.copy2(fpath, out)
                extracted_total += 1
            elif f.lower().endswith(('.avi', '.mp4')):
                try:
                    cap = cv2.VideoCapture(fpath)
                    # Extract 3 frames per video
                    for frame_idx in [0, 15, 29]:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                        ret, frame = cap.read()
                        if ret:
                            out = os.path.join(
                                real_dir,
                                f"midv_{extracted_total:04d}.jpg"
                            )
                            cv2.imwrite(out, frame)
                            extracted_total += 1
                    cap.release()
                except Exception as e:
                    print(f"  Frame extract error: {e}")

    print(f"  Total images so far: {extracted_total}")

print(f"\n{'='*50}")
print(f"MIDV-500 download complete!")
print(f"Total document images extracted: {extracted_total}")
print(f"Saved to: {real_dir}")
print(f"\nNext step: run  py python/generate_fakes.py")