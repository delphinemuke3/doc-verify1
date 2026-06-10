from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

o = Options()
o.add_argument('--headless')
o.add_argument('--ignore-certificate-errors')
o.add_argument('--log-level=3')
o.add_experimental_option('excludeSwitches', ['enable-logging'])

d = webdriver.Chrome(options=o)
d.get('https://graduate.rp.ac.rw/?certificate_no=17873')
time.sleep(5)
text = d.find_element(By.TAG_NAME, 'body').text
print(text[:3000])
d.quit()