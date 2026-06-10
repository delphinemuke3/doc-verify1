import cv2, pytesseract
from PIL import Image
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
img = cv2.imread(r'C:\xampp2\htdocs\doc-verify\uploads\doc_6a25c7e1a4778.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
upscaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
text = pytesseract.image_to_string(Image.fromarray(upscaled), config='--oem 3 --psm 6')
print(text[:3000])