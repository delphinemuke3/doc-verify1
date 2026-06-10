from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')

print("Connecting to RP portal...")
d = webdriver.Chrome(options=opts)
d.get('https://graduate.rp.ac.rw/?certificate_no=19941')
try:
    WebDriverWait(d, 12).until(lambda x: len(x.find_element(By.TAG_NAME,'body').text.strip()) > 80)
except Exception:
    time.sleep(8)
t = d.find_element(By.TAG_NAME,'body').text
d.quit()

print("=== RAW PAGE TEXT ===")
print(repr(t[:800]))
print("=== END ===")
print()
print("Line by line:")
for i, line in enumerate(t.splitlines()):
    if line.strip():
        print(f"  [{i}] {repr(line)}")