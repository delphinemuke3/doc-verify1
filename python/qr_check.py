import sys
import json
import os
import cv2
import numpy as np
import re
from urllib.parse import parse_qs, unquote, urlparse

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

TRUSTED_DOMAINS = [
    'graduate.rp.ac.rw', 'graduate.nesa.gov.rw', 'rp.ac.rw', 'ur.ac.rw',
    'ulk.ac.rw', 'utab.ac.rw', 'mku.ac.ke', 'nesa.gov.rw', 'nesa.rw',
    'nida.gov.rw', 'rra.gov.rw', 'rtda.gov.rw', 'gov.rw',
]

INSTITUTION_URL_MAP = {
    'graduate.rp.ac.rw':    'Rwanda Polytechnic',
    'graduate.nesa.gov.rw': 'NESA (National Exam Board)',
    'rp.ac.rw':             'Rwanda Polytechnic',
    'ur.ac.rw':             'University of Rwanda',
    'ulk.ac.rw':            'Universite Libre de Kigali',
    'utab.ac.rw':           'University of Technology and Arts of Byumba',
    'mku.ac.ke':            'Mount Kenya University',
    'nesa.gov.rw':          'NESA (National Exam Board)',
    'nesa.rw':              'NESA (National Exam Board)',
    'nida.gov.rw':          'NIDA (National ID Agency)',
    'rtda.gov.rw':          'RTDA (Driving License Authority)',
    'gov.rw':               'Government of Rwanda',
}

MKU_CERT_PATTERNS = [
    re.compile(r'\b([A-Z]{2,6})/(\d{4})/(\d{4,8})\b'),
    re.compile(r'\b([A-Z]{2,6}T)/(\d{4})/(\d{3,8})\b'),
]

MKU_KEYWORDS = [
    'MOUNT KENYA', 'MKU', 'BACHELOR', 'MASTER', 'DOCTOR',
    'HONOURS', 'DIVISION', 'CONGREGATION', 'UNIVERSITY COUNCIL',
    'SENATE', 'REGISTRAR', 'CHANCELLOR'
]


def detect_mku_data_qr(qr_data):
    qr_upper = qr_data.upper()
    mku_signals = sum(1 for kw in MKU_KEYWORDS if kw in qr_upper)
    if mku_signals < 1:
        return None
    cert_number = None
    cert_year   = None
    for pattern in MKU_CERT_PATTERNS:
        m = pattern.search(qr_data)
        if m:
            cert_number = m.group(0)
            try:
                cert_year = int(m.group(2))
            except Exception:
                cert_year = None
            break
    year_valid = True
    if cert_year and not (1990 <= cert_year <= 2026):
        year_valid = False
    extracted_name = None
    if cert_number:
        after_cert = qr_data[qr_data.find(cert_number) + len(cert_number):].strip()
        name_match = re.match(
            r'([A-Z][A-Z\s]{3,40}?)(?:\s+(?:BACHELOR|MASTER|DOCTOR|SECOND|FIRST|THIRD|PASS))',
            after_cert.upper()
        )
        if name_match:
            extracted_name = name_match.group(1).strip()
        else:
            words = [w for w in after_cert.split() if w.isalpha() and len(w) > 1]
            if len(words) >= 2:
                extracted_name = ' '.join(words[:3])
    if cert_number and year_valid:
        return {'is_mku_data_qr': True, 'cert_number': cert_number, 'cert_year': cert_year,
                'extracted_name': extracted_name, 'format_valid': True,
                'message': f'MKU certificate number validated from QR: {cert_number}'}
    elif cert_number and not year_valid:
        return {'is_mku_data_qr': True, 'cert_number': cert_number, 'cert_year': cert_year,
                'extracted_name': extracted_name, 'format_valid': False,
                'message': f'MKU certificate year {cert_year} is out of valid range'}
    else:
        return {'is_mku_data_qr': True, 'cert_number': None, 'cert_year': None,
                'extracted_name': extracted_name, 'format_valid': False,
                'message': 'MKU QR detected but certificate number not found'}


def decode_qr_opencv(img):
    try:
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(img)
        if data:
            return [data]
    except Exception:
        pass
    return []


def decode_qr_pyzbar(img):
    try:
        from pyzbar.pyzbar import decode
        decoded = decode(img)
        return [d.data.decode('utf-8', errors='ignore') for d in decoded if d.data]
    except Exception:
        pass
    return []


def decode_qr_enhanced(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return []
    all_results = []
    h, w = img.shape[:2]

    def try_decode(candidate, deep=False):
        results = []
        if candidate is None or candidate.size == 0:
            return results
        if len(candidate.shape) == 3:
            gray_candidate = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
        else:
            gray_candidate = candidate
        variants = [candidate, gray_candidate]
        if deep:
            variants.append(cv2.equalizeHist(gray_candidate))
            variants.append(cv2.threshold(gray_candidate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
            variants.append(cv2.adaptiveThreshold(
                gray_candidate, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5))
        scales = (2, 3, 4) if deep else (2,)
        for scale in scales:
            variants.append(cv2.resize(candidate, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC))
            if deep:
                variants.append(cv2.resize(gray_candidate, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC))
        for variant in variants:
            rotations = (
                variant,
                cv2.rotate(variant, cv2.ROTATE_90_CLOCKWISE),
                cv2.rotate(variant, cv2.ROTATE_180),
                cv2.rotate(variant, cv2.ROTATE_90_COUNTERCLOCKWISE),
            ) if deep else (variant,)
            for rotated in rotations:
                results += decode_qr_opencv(rotated)
                results += decode_qr_pyzbar(rotated)
        return results

    all_results += try_decode(img)
    if all_results:
        return list(set(all_results))
    upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    all_results += try_decode(upscaled)
    if all_results:
        return list(set(all_results))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    all_results += try_decode(binary)
    if all_results:
        return list(set(all_results))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    all_results += try_decode(enhanced)
    if all_results:
        return list(set(all_results))
    regions = [
        img[int(h*0.75):h, int(w*0.75):w],
        img[int(h*0.75):h, 0:int(w*0.25)],
        img[0:int(h*0.25), int(w*0.75):w],
        img[0:int(h*0.25), 0:int(w*0.25)],
        img[int(h*0.68):int(h*0.84), int(w*0.35):int(w*0.65)],
        img[int(h*0.70):int(h*0.82), int(w*0.40):int(w*0.60)],
        img[int(h*0.60):int(h*0.90), int(w*0.30):int(w*0.70)],
    ]
    for region in regions:
        if region.size == 0:
            continue
        all_results += try_decode(region, deep=True)
    return list(set(r for r in all_results if r))


def extract_url_from_qr(qr_data):
    url_match = re.search(r'https?://[^\s"\'<>]+', qr_data)
    if url_match:
        return url_match.group(0).strip()
    domain_match = re.search(r'(?:www\.)?[\w\-]+\.(?:ac\.rw|gov\.rw|rw|ke)[^\s]*', qr_data)
    if domain_match:
        return 'https://' + domain_match.group(0).strip()
    return None


def extract_url_from_image_text(image_path):
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    except Exception:
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    crops = [
        img[int(h * 0.82):h, 0:w],
        img[int(h * 0.70):h, int(w * 0.20):int(w * 0.80)],
        img,
    ]
    for crop in crops:
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            text = pytesseract.image_to_string(gray, config='--oem 3 --psm 6')
        except Exception:
            continue
        compact = re.sub(r'\s+', '', text)
        if re.search(r'graduate\.?nesa\.?gov\.?rw', compact, re.IGNORECASE):
            return 'https://graduate.nesa.gov.rw'
        url = extract_url_from_qr(compact)
        if url:
            return url
    return None


def normalize_nesa_serial(raw_text):
    if not raw_text:
        return None
    compact = re.sub(r'[^A-Za-z0-9]', '', raw_text).upper()
    candidates = re.findall(r'A[A-Z0-9]{6,12}', compact)
    for candidate in candidates:
        if sum(ch.isdigit() for ch in candidate[:9]) < 4:
            continue
        normalized = candidate[:9].translate(str.maketrans({
            'O': '0', 'Q': '0', 'I': '1', 'L': '1', 'N': '2',
            'Z': '7', 'S': '5', 'B': '8', 'E': '8'
        }))
        if re.fullmatch(r'A\d{8}', normalized):
            return normalized
    spaced = re.search(r'A\s*([0-9OQILNZSBE]\s*){8}', raw_text.upper(), flags=re.IGNORECASE)
    if spaced:
        return normalize_nesa_serial(spaced.group(0))
    return None


def extract_nesa_serial_from_image_text(image_path):
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    except Exception:
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    crops = [
        img[int(h * 0.82):h, 0:w],
        img[int(h * 0.72):h, int(w * 0.55):w],
        img[int(h * 0.78):h, int(w * 0.60):w],
        img,
    ]
    for crop in crops:
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            for psm in (6, 7, 11):
                text = pytesseract.image_to_string(gray, config=f'--oem 3 --psm {psm}')
                serial = normalize_nesa_serial(text)
                if serial:
                    return serial
        except Exception:
            continue
    return None


def extract_nesa_serial_from_url(url):
    if not url:
        return None
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key in ('serial', 'certificate', 'cert', 'number', 'id', 'ref'):
            values = query.get(key) or query.get(key.upper()) or []
            for val in values:
                serial = normalize_nesa_serial(val)
                if serial:
                    return serial
        for part in parsed.path.split('/'):
            serial = normalize_nesa_serial(part)
            if serial:
                return serial
    except Exception:
        pass
    return None


def clean_person_name(raw_name):
    if not raw_name:
        return None
    decoded = unquote(str(raw_name))
    decoded = decoded.replace('+', ' ').replace('_', ' ').replace('-', ' ')
    decoded = re.sub(r'[^A-Za-z\s\']', ' ', decoded)
    decoded = re.sub(r'\s+', ' ', decoded).strip()
    decoded = re.split(
        r'\b(?:BACHELOR|MASTER|DOCTOR|DIPLOMA|CERTIFICATE|DEGREE|FACULTY|SCHOOL'
        r'|PROGRAM|PROGRAMME|REGISTRATION|REG\s*NO|DEPARTMENT|COLLEGE|OPTION'
        r'|GRADE|DIVISION|UPPER|LOWER|CAMPUS|INSTITUTE)\b',
        decoded, maxsplit=1, flags=re.IGNORECASE
    )[0].strip()
    if len(decoded) < 4:
        return None
    name_upper = decoded.upper()
    blocked_words = {
        'CERTIFICATE', 'VERIFY', 'VERIFIED', 'VALID', 'ONLINE', 'DOCUMENT',
        'UNIVERSITY', 'TECHNOLOGY', 'ARTS', 'BYUMBA', 'UTAB', 'RWANDA',
        'INFORMATION', 'CONTACT', 'PLEASE', 'EMAIL', 'CALL', 'OFFICER',
        'COMMUNICATION', 'DEPARTMENT', 'COLLEGE', 'OPTION', 'GRADE',
        'DIVISION', 'INSTITUTE', 'CAMPUS', 'POLYTECHNIC',
    }
    words = [w for w in name_upper.split() if len(w) > 1]
    if len(words) < 2:
        return None
    if any(w in blocked_words for w in words):
        return None
    if len(words) > 5:
        return None
    return ' '.join(words)


def extract_name_from_url(url):
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
    except Exception:
        return None
    name_keys = [
        'name', 'names', 'full_name', 'fullname', 'student', 'student_name',
        'student_names', 'studentnames', 'student_full_name', 'studentfullname',
        'holder', 'holder_name', 'candidate', 'candidate_name', 'graduate',
        'graduate_name', 'beneficiary', 'owner', 'owner_name', 'degree_owner'
    ]
    normalized_query = {k.lower(): v for k, v in query.items()}
    for key in name_keys:
        values = normalized_query.get(key)
        if not values:
            continue
        for value in values:
            extracted = clean_person_name(value)
            if extracted:
                return extracted
    first_values = normalized_query.get('first_name') or normalized_query.get('firstname') or []
    last_values  = normalized_query.get('last_name')  or normalized_query.get('lastname')  or []
    if first_values and last_values:
        extracted = clean_person_name(f"{first_values[0]} {last_values[0]}")
        if extracted:
            return extracted
    path_parts = [p for p in parsed.path.split('/') if p]
    for part in reversed(path_parts):
        extracted = clean_person_name(part)
        if extracted:
            return extracted
    return None


def extract_name_before_registration(page_text):
    lines = [re.sub(r'\s+', ' ', line).strip() for line in page_text.upper().splitlines()]
    lines = [line for line in lines if line]
    for index, line in enumerate(lines):
        if re.search(r'\b(?:REGISTRATION\s+NUMBER|REG\s*NO|REGISTRATION\s+NO)\b', line):
            for prev_index in range(index - 1, max(-1, index - 6), -1):
                extracted = clean_person_name(lines[prev_index])
                if extracted:
                    return extracted
    return None


def identify_institution_from_url(url):
    url_lower = url.lower()
    for domain, institution in INSTITUTION_URL_MAP.items():
        if domain in url_lower:
            return institution, domain
    return None, None


def is_trusted_url(url):
    url_lower = url.lower()
    for domain in TRUSTED_DOMAINS:
        if domain in url_lower:
            return True
    return False


def is_utab_url(url):
    return 'utab.ac.rw' in (url or '').lower()


def extract_certificate_no(url):
    match = re.search(r'certificate_no=(\w+)', url)
    return match.group(1) if match else None


def extract_name_from_page(page_text, candidate_name=""):
    text_upper = page_text.upper()
    _STOP = (
        r'(?:PROGRAM(?:ME)?|FACULTY|SCHOOL|CLASS|DIVISION|YEAR|STATUS|VALID'
        r'|CERTIFICATE|BACHELOR|MASTER|DOCTOR|DIPLOMA|REGISTRATION|REG\s*NO'
        r'|AWARD|GRADUATION|DEPARTMENT|MAJOR|GPA|CGPA|GRADE|INDEX'
        r'|EXAMINATION|AGGREGATE|MENTION|CONGREGATION|COLLEGE|INSTITUTE'
        r'|CAMPUS|STUDY|COURSE|QUALIFICATION|LEVEL|HONOURS|DISTINCTION)'
    )
    _LABEL = (
        r'(?:STUDENT\s+NAMES?|STUDENT\s+NAME|GRADUATE\s+NAME'
        r'|FULL\s+NAME|HOLDER\s+NAME|CANDIDATE\s+NAME|NAMES?)'
    )
    name_patterns = [
        r'([A-Z][A-Z\s\']{3,60}?)\s+REGISTRATION\s+NUMBER',
        r'([A-Z][A-Z\s\']{3,60}?)\s+REG\s*NO',
        _LABEL + r'\s*[:\-]?\s*([A-Z][A-Z\s\']{2,60}?)(?=\s+' + _STOP + r'|\s*$|\n|<)',
        r'(?:STUDENT|HOLDER|CANDIDATE|GRADUATE)\s*:\s*([A-Z][A-Z\s\']{2,60}?)(?=\s+' + _STOP + r'|\s*$|\n|<)',
        r'(?:AWARDED\s+TO|CONFERRED\s+ON|ISSUED\s+TO|CERTIFY\s+THAT)\s*[:\-]?\s*([A-Z][A-Z\s\']{2,60}?)(?=\s+' + _STOP + r'|\s*$|\n|<)',
    ]
    extracted_name = None
    labels = {
        'NAME', 'NAMES', 'FULL NAME', 'STUDENT NAME', 'STUDENT NAMES',
        'HOLDER NAME', 'CANDIDATE NAME', 'GRADUATE NAME', 'GRADUATE',
    }
    lines = [re.sub(r'\s+', ' ', line).strip() for line in text_upper.splitlines()]
    lines = [line for line in lines if line]
    for index, line in enumerate(lines[:-1]):
        normalized = line.rstrip(':').strip()
        if normalized in labels:
            candidate = clean_person_name(lines[index + 1])
            if candidate:
                extracted_name = candidate
                break
    for pat in name_patterns:
        if extracted_name:
            break
        m = re.search(pat, text_upper, re.MULTILINE)
        if m:
            candidate = clean_person_name(m.group(1))
            if candidate:
                extracted_name = candidate
                break
    if not extracted_name:
        extracted_name = extract_name_before_registration(page_text)

    name_match        = None
    name_match_detail = ''
    if extracted_name and candidate_name:
        cand_upper = candidate_name.upper().strip()
        parts      = [p for p in cand_upper.split() if len(p) > 2]
        matched    = sum(1 for p in parts if p in extracted_name)
        ratio      = matched / len(parts) if parts else 0
        name_match = ratio >= 0.6
        name_match_detail = (
            f"Name on certificate: '{extracted_name}' — "
            f"{'MATCHES' if name_match else 'DOES NOT MATCH'} candidate '{candidate_name}'"
        )
    return extracted_name, name_match, name_match_detail


def _verify_rp_requests_fallback(url, candidate_name=""):
    try:
        import requests
        from bs4 import BeautifulSoup
        headers  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=12, verify=False)
        if response.status_code != 200:
            return {'reachable': True, 'record_found': False,
                    'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                    'message': f'RP portal HTTP {response.status_code}', 'method': 'requests_fallback'}
        page_text  = BeautifulSoup(response.text, 'html.parser').get_text('\n')
        page_upper = page_text.upper()
        rp_success       = ['STUDENT NAME', 'STUDENT NAMES', 'NAMES', 'GRADUATE',
                            'CERTIFICATE NO', 'CERTIFICATE VERIFIED', 'VALID',
                            'RWANDA POLYTECHNIC', 'NAME:', 'CODE:']
        error_indicators = ['NOT FOUND', 'INVALID', 'NO RECORD', 'CERTIFICATE NOT FOUND']
        found_cert  = any(s in page_upper for s in rp_success)
        found_error = any(e in page_upper for e in error_indicators)
        extracted_name, name_match, name_match_detail = extract_name_from_page(page_text, candidate_name)
        return {
            'reachable':         True,
            'record_found':      found_cert and not found_error,
            'extracted_name':    extracted_name,
            'name_match':        name_match,
            'name_match_detail': name_match_detail,
            'message':           'RP certificate record found (requests fallback)' if found_cert else 'Record not confirmed',
            'method':            'requests_fallback'
        }
    except Exception as e:
        return {'reachable': False, 'record_found': None,
                'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                'message': f'RP requests fallback error: {str(e)}', 'method': 'requests_fallback_error'}


def verify_rp_with_selenium(url, candidate_name=""):
    """
    FIXED: Retries once if Selenium returns empty page (Chrome init timing).
    Falls back to requests if both attempts fail.
    Falls back to requests if page loads but name extraction fails.
    """
    def _attempt(url):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        import time

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(25)
        try:
            driver.get(url)
            try:
                WebDriverWait(driver, 12).until(
                    lambda d: len(d.find_element(By.TAG_NAME, 'body').text.strip()) > 80
                )
            except Exception:
                time.sleep(8)
            return driver.find_element(By.TAG_NAME, 'body').text
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    try:
        page_text = ""

        # Attempt 1
        try:
            page_text = _attempt(url)
        except Exception:
            pass

        # Attempt 2 if first returned nothing
        if len(page_text.strip()) < 80:
            try:
                page_text = _attempt(url)
            except Exception:
                pass

        # Both attempts failed — use requests fallback
        if len(page_text.strip()) < 80:
            return _verify_rp_requests_fallback(url, candidate_name)

        page_upper = page_text.upper()

        rp_success = [
            'CERTIFICATE VERIFIED', 'VALID CERTIFICATE', 'VALID',
            'STUDENT NAME', 'STUDENT NAMES', 'NAMES', 'GRADUATE',
            'CERTIFICATE NO', 'CERTIFICATE NUMBER', 'RWANDA POLYTECHNIC',
            'NAME:', 'CODE:', 'REGISTRATION NUMBER:',
        ]
        error_indicators = ['NOT FOUND', 'INVALID', 'NO RECORD', 'DOES NOT EXIST', 'CERTIFICATE NOT FOUND']

        found_cert  = any(sig in page_upper for sig in rp_success)
        found_error = any(err in page_upper for err in error_indicators)

        if found_error and not found_cert:
            return {'reachable': True, 'record_found': False,
                    'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                    'message': 'Certificate not found in RP records', 'method': 'selenium'}

        extracted_name, name_match, name_match_detail = extract_name_from_page(
            page_text, candidate_name
        )

        # Page loaded but name extraction failed — requests fallback often parses better
        if found_cert and extracted_name is None:
            fallback = _verify_rp_requests_fallback(url, candidate_name)
            if fallback.get('extracted_name'):
                return fallback

        return {
            'reachable':         True,
            'record_found':      found_cert and not found_error,
            'extracted_name':    extracted_name,
            'name_match':        name_match,
            'name_match_detail': name_match_detail or (
                'Rwanda Polytechnic confirmed certificate exists. '
                'Name extraction failed — manual check recommended.'
            ),
            'message': 'Certificate verified by Rwanda Polytechnic portal' if found_cert else 'Record not confirmed',
            'method': 'selenium'
        }

    except ImportError:
        return _verify_rp_requests_fallback(url, candidate_name)
    except Exception as e:
        return {'reachable': False, 'record_found': None,
                'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                'message': f'Selenium error: {str(e)}', 'method': 'selenium_error'}


def verify_nesa_online(serial, candidate_name=""):
    if not serial:
        return {'reachable': True, 'record_found': None,
                'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                'message': 'NESA verification page requires certificate number', 'method': 'nesa_post'}
    try:
        import requests
        from bs4 import BeautifulSoup
        response = requests.post(
            'https://graduate.nesa.gov.rw/',
            data={'serial': serial},
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
            timeout=15, verify=False
        )
        text  = BeautifulSoup(response.text, 'html.parser').get_text('\n')
        upper = text.upper()
        found     = 'VALID' in upper and 'GRADUATE NAME' in upper
        not_found = any(token in upper for token in ('INVALID', 'NOT FOUND', 'NO RECORD'))
        extracted_name = None
        match = re.search(
            r'GRADUATE\s+NAME\s*[:\s]+([A-Z][A-Z\s\'-]{3,80}?)(?=\s+'
            r'(?:INDEX\s+NUMBER|EXAMINATION\s+AUTHORITY|SCHOOL|EXAM\s+YEAR|MENTION|AGGREGATE)|$)',
            upper, re.MULTILINE
        )
        if match:
            extracted_name = clean_person_name(match.group(1))
        if not extracted_name:
            lines = [l.strip() for l in upper.splitlines() if l.strip()]
            for idx, line in enumerate(lines[:-1]):
                if re.search(r'GRADUATE\s+NAME', line):
                    after_colon = re.split(r'[:\-]', line, maxsplit=1)
                    if len(after_colon) > 1 and after_colon[1].strip():
                        extracted_name = clean_person_name(after_colon[1])
                    if not extracted_name:
                        extracted_name = clean_person_name(lines[idx + 1])
                    break
        name_match = None
        name_match_detail = ''
        if extracted_name and candidate_name:
            name_match = match_names(extracted_name, candidate_name)
            name_match_detail = (
                f"Name on certificate: '{extracted_name}' - "
                f"{'MATCHES' if name_match else 'DOES NOT MATCH'} candidate '{candidate_name}'"
            )
        return {'reachable': True, 'record_found': found and not not_found,
                'extracted_name': extracted_name, 'name_match': name_match,
                'name_match_detail': name_match_detail,
                'message': 'NESA certificate verified online' if found else 'NESA record not confirmed',
                'method': 'nesa_post'}
    except Exception as e:
        return {'reachable': False, 'record_found': None,
                'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                'message': f'Could not reach NESA: {str(e)}', 'method': 'nesa_post_error'}


def verify_url_online(url, candidate_name="", nesa_serial=None):
    trusted   = is_trusted_url(url)
    link_name = extract_name_from_url(url) if trusted else None

    if 'graduate.nesa.gov.rw' in url or 'nesa.gov.rw' in url:
        return verify_nesa_online(nesa_serial, candidate_name)

    if 'graduate.rp.ac.rw' in url:
        result = verify_rp_with_selenium(url, candidate_name)
        if result.get('reachable'):
            if link_name and not result.get('extracted_name'):
                result['extracted_name'] = link_name
            return result

    try:
        import requests
        from bs4 import BeautifulSoup
        headers  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup       = BeautifulSoup(response.text, 'html.parser')
            page_text  = soup.get_text()
            page_upper = page_text.upper()
            cert_indicators  = ['CERTIFICATE', 'DIPLOMA', 'DEGREE', 'VERIFIED', 'GRADUATE', 'VALID']
            error_indicators = ['NOT FOUND', 'INVALID', 'ERROR', 'NO RECORD', '404']
            found_indicators = [i for i in cert_indicators if i in page_upper]
            found_errors     = [i for i in error_indicators if i in page_upper]
            if found_errors and not found_indicators:
                return {'reachable': True, 'record_found': False,
                        'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                        'message': 'Record not found — possible fake', 'method': 'requests'}
            elif found_indicators:
                extracted_name, name_match, name_match_detail = extract_name_from_page(page_text, candidate_name)
                if not extracted_name:
                    extracted_name = link_name
                if extracted_name and candidate_name and name_match is None:
                    name_match = match_names(extracted_name, candidate_name)
                    name_match_detail = (
                        f"Name on certificate: '{extracted_name}' - "
                        f"{'MATCHES' if name_match else 'DOES NOT MATCH'} candidate '{candidate_name}'"
                    )
                return {'reachable': True, 'record_found': True,
                        'extracted_name': extracted_name, 'name_match': name_match,
                        'name_match_detail': name_match_detail,
                        'message': 'Certificate record found online', 'method': 'requests'}
            else:
                name_match = None
                name_match_detail = ''
                if link_name and candidate_name:
                    name_match = match_names(link_name, candidate_name)
                    name_match_detail = (
                        f"Name on certificate: '{link_name}' - "
                        f"{'MATCHES' if name_match else 'DOES NOT MATCH'} candidate '{candidate_name}'"
                    )
                return {'reachable': True, 'record_found': None,
                        'extracted_name': link_name, 'name_match': name_match,
                        'name_match_detail': name_match_detail,
                        'message': 'URL reachable but could not confirm record', 'method': 'requests'}
        else:
            return {'reachable': True, 'record_found': False,
                    'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                    'message': f'HTTP {response.status_code}', 'method': 'requests'}
    except Exception as e:
        return {'reachable': False, 'record_found': None,
                'extracted_name': None, 'name_match': None, 'name_match_detail': '',
                'message': f'Could not reach URL: {str(e)}', 'method': 'requests_error'}


def match_names(name1, name2):
    if not name1 or not name2:
        return None
    n1 = name1.upper().strip()
    n2 = name2.upper().strip()
    if n1 == n2:
        return True
    parts1 = [p for p in n1.split() if len(p) > 2]
    parts2 = [p for p in n2.split() if len(p) > 2]
    if not parts1 or not parts2:
        return None
    matched = sum(1 for p in parts1 if p in n2)
    ratio = matched / len(parts1)
    return ratio >= 0.6


def check_qr(image_path, candidate_name=""):
    try:
        if not os.path.exists(image_path):
            return {"success": False, "error": "File not found", "qr_found": False,
                    "trusted": False, "issues": [], "positives": [], "qr_data": None}

        issues    = []
        positives = []
        nesa_serial = extract_nesa_serial_from_image_text(image_path)

        qr_strings = decode_qr_enhanced(image_path)
        link_from_text = False
        if not qr_strings:
            fallback_url = extract_url_from_image_text(image_path)
            if fallback_url:
                qr_strings = [fallback_url]
                link_from_text = True

        if not qr_strings:
            return {"success": True, "qr_found": False, "trusted": False,
                    "verified_online": False, "name_match": None,
                    "institution": None, "qr_url": None, "qr_data": None,
                    "issues": [], "positives": []}

        qr_data = qr_strings[0]
        positives.append("Verification link found on document" if link_from_text else "QR code detected on document")

        mku_result = detect_mku_data_qr(qr_data)
        if mku_result:
            cert_number    = mku_result.get('cert_number')
            format_valid   = mku_result.get('format_valid', False)
            extracted_name = mku_result.get('extracted_name')
            name_match = None
            if extracted_name and candidate_name:
                name_match = match_names(extracted_name, candidate_name)
                if name_match is True:
                    positives.append(f"✓ NAME VERIFIED via MKU QR: '{extracted_name}' matches candidate")
                elif name_match is False:
                    issues.append(f"⚠ NAME MISMATCH via MKU QR: QR shows '{extracted_name}' but candidate is '{candidate_name}' — possible borrowed certificate!")
            if format_valid and cert_number:
                positives.append(f"✓ MKU certificate number validated from QR: {cert_number}")
                positives.append("Mount Kenya University certificate data verified from embedded QR")
            else:
                issues.append(mku_result.get('message', 'MKU QR format invalid'))
            return {"success": True, "qr_found": True, "trusted": format_valid and name_match is not False,
                    "verified_online": False, "name_match": name_match, "extracted_name": extracted_name,
                    "institution": "Mount Kenya University", "matched_domain": "mku.ac.ke",
                    "qr_url": None, "qr_data": qr_data[:200], "online_status": mku_result.get('message', ''),
                    "cert_number": cert_number, "issues": issues, "positives": positives}

        qr_url = extract_url_from_qr(qr_data)
        if not qr_url:
            return {"success": True, "qr_found": True, "trusted": False,
                    "verified_online": False, "name_match": None,
                    "institution": None, "qr_url": None, "qr_data": qr_data,
                    "issues": ["QR code found but contains no recognizable URL"], "positives": positives}

        positives.append(f"QR code links to: {qr_url[:70]}")
        extracted_name_from_link = extract_name_from_url(qr_url)
        if extracted_name_from_link:
            positives.append(f"Certificate holder from QR link: {extracted_name_from_link}")

        serial_from_url = extract_nesa_serial_from_url(qr_url)
        if serial_from_url:
            nesa_serial = serial_from_url

        trusted = is_trusted_url(qr_url)
        institution, matched_domain = identify_institution_from_url(qr_url)

        if trusted and institution:
            positives.append(f"QR URL belongs to trusted institution: {institution}")
        elif trusted:
            positives.append("QR URL belongs to a trusted Rwandan government domain")
        else:
            issues.append(f"QR URL domain is NOT recognized: {qr_url}")

        online_result        = verify_url_online(qr_url, candidate_name, nesa_serial)
        verified_online      = False
        name_match           = None
        final_extracted_name = extracted_name_from_link

        if online_result.get('reachable'):
            if online_result.get('record_found') is True:
                verified_online      = True
                extracted_name       = online_result.get('extracted_name') or extracted_name_from_link
                final_extracted_name = extracted_name
                name_match           = online_result.get('name_match')
                name_detail          = online_result.get('name_match_detail', '')

                positives.append(f"✓ ONLINE VERIFIED: Certificate record confirmed at {matched_domain or qr_url}")

                if extracted_name and candidate_name and name_match is None:
                    name_match  = match_names(extracted_name, candidate_name)
                    name_detail = (
                        f"Name on certificate: '{extracted_name}' - "
                        f"{'MATCHES' if name_match else 'DOES NOT MATCH'} candidate '{candidate_name}'"
                    )

                if extracted_name:
                    if name_match is True:
                        positives.append(f"✓ NAME VERIFIED ONLINE: {name_detail}")
                    elif name_match is False:
                        issues.append(f"⚠ NAME MISMATCH ONLINE: {name_detail} — This may be a borrowed certificate!")
                    else:
                        positives.append(f"Certificate holder: {extracted_name}")
                elif candidate_name:
                    positives.append("Certificate verified online — name extraction not available (manual name check recommended)")

            elif online_result.get('record_found') is False:
                issues.append("Online check: Certificate not found in institution records — possible fake or altered document")
            else:
                positives.append("QR URL reachable — verify manually at: " + qr_url)
        else:
            positives.append("QR URL could not be reached (network issue) — verify manually at: " + qr_url)

        if final_extracted_name and candidate_name and name_match is None:
            name_match = match_names(final_extracted_name, candidate_name)
            if name_match is True:
                positives.append(f"Name from QR link matches candidate: {final_extracted_name}")
            else:
                issues.append(f"Name mismatch from QR link: QR shows '{final_extracted_name}' but candidate is '{candidate_name}'")

        final_trusted = trusted and (verified_online or online_result.get('record_found') is not False)
        if name_match is False:
            final_trusted = False

        return {
            "success":         True,
            "qr_found":        True,
            "trusted":         final_trusted,
            "verified_online": verified_online,
            "name_match":      name_match,
            "extracted_name":  final_extracted_name,
            "institution":     institution,
            "matched_domain":  matched_domain,
            "qr_url":          qr_url,
            "qr_data":         qr_data[:200] if qr_data else None,
            "nesa_serial":     nesa_serial,
            "online_status":   online_result.get('message', ''),
            "issues":          issues,
            "positives":       positives
        }

    except Exception as e:
        return {"success": False, "error": str(e), "qr_found": False, "trusted": False,
                "verified_online": False, "name_match": None,
                "issues": [f"QR check error: {str(e)}"], "positives": [], "qr_data": None}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: qr_check.py <image_path> [candidate_name]",
                          "qr_found": False, "trusted": False, "issues": [], "positives": []}))
        sys.exit(1)
    image_path     = sys.argv[1]
    candidate_name = sys.argv[2] if len(sys.argv) > 2 else ""
    result = check_qr(image_path, candidate_name)
    print(json.dumps(result))