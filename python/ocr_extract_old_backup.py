import sys
import json
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import re
import cv2
import numpy as np
from difflib import SequenceMatcher

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

RWANDA_INSTITUTIONS = {
    "universities": [
        "UNIVERSITY OF RWANDA", "UR-",
        "KIGALI INDEPENDENT UNIVERSITY", "ULK",
        "UNIVERSITE LIBRE DE KIGALI",
        "INES RUHENGERI", "INES",
        "INSTITUT D'ENSEIGNEMENT SUPERIEUR DE RUHENGERI",
        "ADVENTIST UNIVERSITY OF CENTRAL AFRICA", "AUCA",
        "HIGHER INSTITUTE OF AGRICULTURE", "ISAE",
        "KIGALI HEALTH INSTITUTE", "KHI",
        "SCHOOL OF FINANCE AND BANKING", "SFB",
        "UNIVERSITE CATHOLIQUE DE KABGAYI", "UCK",
        "UNIVERSITY OF TOURISM TECHNOLOGY", "UTB",
        "AFRICAN LEADERSHIP UNIVERSITY", "ALU",
        "CARNEGIE MELLON UNIVERSITY AFRICA", "CMU AFRICA",
        "MOUNT KENYA UNIVERSITY", "MKU",
        "UNIVERSITY OF TECHNOLOGY AND ARTS", "UTAB",
    ],
    "polytechnics": [
        "RWANDA POLYTECHNIC", "POLYTECHNIC",
        "INTEGRATED POLYTECHNIC REGIONAL COLLEGE", "IPRC",
        "IPRC KIGALI", "IPRC HUYE", "IPRC MUSANZE",
        "IPRC RUBAVU", "IPRC RWAMAGANA", "IPRC TUMBA",
        "VOCATIONAL TRAINING CENTER", "VTC",
        "WDA", "WORKFORCE DEVELOPMENT AUTHORITY",
        "POLYTEC",
    ],
    "secondary": [
        "ECOLE DES SCIENCES", "LYCEE", "COLLEGE SAINT ANDRE",
        "GROUPE SCOLAIRE", "GS OFFICIEL", "SECONDARY SCHOOL",
        "HIGH SCHOOL", "SENIOR SIX",
        "NESA", "NATIONAL EXAMINATION",
        "RWANDA EDUCATION BOARD", "REB",
    ],
    "government": [
        "REPUBLIC OF RWANDA", "REPUBULIKA Y'U RWANDA",
        "GOVERNMENT OF RWANDA", "MINEDUC",
        "HIGHER EDUCATION COUNCIL", "HEC",
        "NATIONAL IDENTIFICATION AGENCY", "NIDA",
        "RWANDA NATIONAL POLICE", "RNP",
    ]
}

INSTITUTION_SHORT_CODES = [
    "RP", "UR", "ULK", "MKU", "UTAB", "AUCA", "INES",
    "IPRC", "WDA", "REB", "HEC", "NIDA", "ALU", "ISAE",
    "VTC", "SFB", "UCK", "UTB", "KHI",
]

INSTITUTION_FRAGMENTS = [
    "POLYTECHNIC", "POLYTEC", "RWANDA POLY",
    "UNIV OF RWANDA", "KIGALI UNIV",
    "IPRC", "ISAE", "AUCA", "INES", "ULK", "ALU",
    "WDA", "REB", "NIDA", "HEC", "MKU", "UTAB",
    "RP.AC.RW", "UR.AC.RW", "MINEDUC",
    "GRADUATE.RP",
]

RWANDA_ID_KEYWORDS = [
    'REPUBLIC OF RWANDA', 'REPUBULIKA', 'NATIONAL ID',
    'INDANGAMUNTU', 'NID', 'NIDA', 'DATE OF BIRTH',
    'ITARIKI', 'AMAZINA', 'NATIONALITY', 'UBWENEGIHUGU',
    'RWANDA', 'VALID', 'DISTRICT', 'AKARERE', 'SEX', 'UBWOKO'
]

RWANDA_CERT_KEYWORDS = [
    'CERTIFICATE', 'DIPLOMA', 'DEGREE', 'BACHELOR', 'MASTER',
    'ADVANCED DIPLOMA', 'THIS IS TO CERTIFY', 'VICE CHANCELLOR',
    'RECTOR', 'REGISTRAR', 'CONGREGATION', 'UNIVERSITY',
    'INSTITUTE', 'COLLEGE', 'RWANDA', 'AWARD', 'CONFERRED',
    'ACADEMIC', 'GRADUATION', 'CERTIFY', 'SATISFIED',
    'HIGHER DIPLOMA', 'HONOURS', 'DISTINCTION', 'FACULTY',
]

RWANDA_TRANSCRIPT_KEYWORDS = [
    'TRANSCRIPT', 'ACADEMIC RECORD', 'GRADE', 'CREDIT',
    'SEMESTER', 'GPA', 'CGPA', 'PASS', 'DISTINCTION',
    'MODULE', 'COURSE', 'STUDENT', 'MARKS', 'SCORE'
]

AUTH_KEYWORDS = [
    'VICE CHANCELLOR', 'DEPUTY VICE CHANCELLOR',
    'PRO-VICE CHANCELLOR', 'RECTOR', 'REGISTRAR',
    'PRINCIPAL', 'DIRECTOR', 'PROVOST',
    'CHARGE OF ACADEMICS', 'CHARGE OF ACADEMIC',
    'INSTITUTIONAL ADVANCEMENT', 'ACADEMICS RESEARCH'
]

COMMON_NAME_WORDS = {
    'REPUBLIC', 'RWANDA', 'OF', 'THE', 'NATIONAL', 'ID', 'DIPLOMA', 'CERTIFICATE',
    'TRANSCRIPT', 'DATE', 'BIRTH', 'NAME', 'AMAZINA', 'NOM', 'PRENOM', 'GRADE',
    'UNIVERSITY', 'INSTITUTE', 'COLLEGE', 'POLYTECHNIC', 'SCHOOL', 'DEGREE',
    'AWARDED', 'REGISTRAR', 'RECTOR', 'VICE', 'CHANCELLOR', 'DIRECTOR', 'YEAR',
    'STUDENT', 'MARKS', 'CGPA', 'GPA', 'COURSE', 'CANDIDATE', 'NUMBER', 'NIDA',
    'GOVERNMENT', 'MINISTRY', 'MINEDUC'
}

def normalize_name_text(text):
    return re.sub(r"[^A-Z\s']+", ' ', text.upper()).strip()


def split_name_parts(name):
    return [p for p in re.findall(r"\b[A-Z']{2,}\b", name.upper()) if p not in COMMON_NAME_WORDS]


def exact_name_in_text(name, text):
    name = name.strip()
    if not name:
        return False
    return re.search(r"\b" + re.escape(name) + r"\b", text) is not None


def compact_letters(value):
    return re.sub(r"[^A-Z]+", "", value.upper())


def best_compact_similarity(needle, haystack):
    """
    Sliding-window compact similarity.

    FIX: minimum window size is now max(len(needle)-1, len(needle))
    i.e. window must be AT LEAST as long as the needle itself.
    Previously min_len = max(3, n-3) allowed a 4-char name to match a
    3-char window (e.g. 'RENE' vs 'REE' from 'THREE') — producing 0.857.
    Now the window must be >= needle length, preventing sub-word matches.
    """
    needle_c   = compact_letters(needle)
    haystack_c = compact_letters(haystack)
    if not needle_c or not haystack_c:
        return 0.0
    if needle_c in haystack_c:
        return 1.0

    n    = len(needle_c)
    best = 0.0
    # FIX: window must be >= needle length (was: max(3, n-3))
    min_len = n
    max_len = min(len(haystack_c), n + 3)

    for size in range(min_len, max_len + 1):
        for start in range(0, len(haystack_c) - size + 1):
            ratio = SequenceMatcher(None, needle_c, haystack_c[start:start + size]).ratio()
            if ratio > best:
                best = ratio
                if best >= 0.95:
                    return best
    return best


def token_word_match(token, text_upper, threshold=0.88):
    """
    Check whether a name token matches any individual WORD in the document
    at >= threshold similarity. This prevents 'RENE' matching document-level
    compact text that happens to contain 'RE' substrings.

    Returns (matched: bool, best_word: str, best_score: float)
    """
    token_c = compact_letters(token)
    if not token_c:
        return False, '', 0.0

    best_score = 0.0
    best_word  = ''
    # Extract individual words (not the full compact blob)
    words = re.findall(r"\b[A-Z']{2,}\b", text_upper)
    for word in words:
        word_c = compact_letters(word)
        if not word_c:
            continue
        # Direct substring
        if token_c in word_c or word_c in token_c:
            ratio = min(len(token_c), len(word_c)) / max(len(token_c), len(word_c))
            if ratio > best_score:
                best_score = ratio
                best_word  = word
            if ratio >= threshold:
                return True, word, ratio
        # SequenceMatcher on equal-length or close-length pairs only
        ratio = SequenceMatcher(None, token_c, word_c).ratio()
        if ratio > best_score:
            best_score = ratio
            best_word  = word
    return best_score >= threshold, best_word, best_score


def extract_person_names(text):
    text_upper = text.upper()
    names = set()

    label_patterns = [
        r"(?:AMAZINA|NAME|FULL NAME|GIVEN NAME|NOM(?:\s+COMPLET)?|PRENOM|IZINA)\s*[:\-]?\s*([A-Z][A-Z\s']{3,})",
        r"(?:NAME OF HOLDER|HOLDER NAME|PERSON NAME)\s*[:\-]?\s*([A-Z][A-Z\s']{3,})",
    ]
    for pat in label_patterns:
        for match in re.findall(pat, text_upper):
            cleaned = ' '.join(
                w for w in re.sub(r"[^A-Z\s']+", ' ', match).split()
                if len(w) > 1 and w not in COMMON_NAME_WORDS
            ).strip()
            if len(cleaned) > 1:
                names.add(cleaned)

    for line in text_upper.splitlines():
        line = line.strip()
        if not line:
            continue
        words = [w for w in re.findall(r"\b[A-Z']{2,}\b", line) if w not in COMMON_NAME_WORDS]
        if 2 <= len(words) <= 4:
            candidate_line = ' '.join(words)
            # Filter out OCR noise lines:
            # 1. Skip lines with single-char tokens (border artifacts like "S S R E")
            if any(len(w) == 1 for w in words):
                continue
            # 2. Skip lines where any token looks like a product/field code
            #    (all-caps run > 12 chars with no vowels = OCR garbage)
            if any(len(w) > 12 and not re.search(r'[AEIOU]', w) for w in words):
                continue
            # 3. Skip lines that contain digits anywhere (not a clean name)
            if re.search(r'\d', line):
                continue
            # 4. Skip lines that are clearly document fields, not names
            field_keywords = {'BUSINESS', 'TECHNOLOGY', 'SCIENCE', 'HONOURS',
                              'BACHELOR', 'MASTER', 'DIVISION', 'ECONOMICS',
                              'COLLEGE', 'INFORMATION', 'CONGREGATION'}
            if any(w in field_keywords for w in words):
                continue
            names.add(candidate_line)

    # Return only names where every token has >= 3 chars (filters "SS RE RS SE")
    clean = [n for n in names if all(len(t) >= 3 for t in n.split())]
    return clean[:4]


def match_candidate_name(text, candidate_name):
    """
    Match candidate_name against OCR text.

    Key fixes vs original:
    1. Short names (< 5 chars, single token) ONLY use exact word-boundary
       matching — no fuzzy/compact matching at all. This prevents 'RENE'
       from matching 'REQUIREMENTS', 'THREE', 'CERTIFY', etc.
    2. Multi-token names use per-token word matching at 0.88 threshold
       (not document-level compact sliding window).
    3. best_compact_similarity now requires window >= needle length.
    4. ocr_name_match threshold raised: adjustment must be >= 10 AND
       at least one token must have a real word-level hit.
    """
    issues          = []
    positives       = []
    score_adjustment = 0
    found_names     = []

    if not candidate_name or not candidate_name.strip():
        return issues, positives, 0, found_names

    # Reject candidates that are too short to be meaningful names
    stripped = candidate_name.strip()
    if len(stripped) < 3:
        return issues, positives, 0, found_names

    text_upper      = normalize_name_text(text)
    candidate_upper = normalize_name_text(candidate_name)
    candidate_parts = split_name_parts(candidate_upper)

    if not candidate_parts:
        return issues, positives, 0, found_names

    found_names = extract_person_names(text)

    # ── Exact full-name match (strongest) ────────────────────────────────────
    exact_candidate_found = exact_name_in_text(candidate_upper, text_upper) or any(
        normalize_name_text(fn) == candidate_upper for fn in found_names
    )

    if exact_candidate_found:
        positives.append(f"Candidate name '{candidate_name}' matches document — identity confirmed")
        return issues, positives, 15, found_names

    # ── Per-token word-level matching ─────────────────────────────────────────
    # Each token in the candidate name must match an actual WORD in the document,
    # not a substring of the compact representation of the full document text.
    total  = len(candidate_parts)
    is_short_single_token = (total == 1 and len(candidate_parts[0]) <= 5)

    token_hits   = []   # (token, matched_word, score)
    token_misses = []

    for part in candidate_parts:
        if is_short_single_token:
            # Short single-token names: require exact word-boundary match only
            # 'RENE' must appear as a complete word in the document
            hit = bool(re.search(r"\b" + re.escape(part) + r"\b", text_upper))
            if hit:
                token_hits.append((part, part, 1.0))
            else:
                token_misses.append(part)
        else:
            # Multi-token or longer names: use per-word fuzzy matching
            threshold = 0.90 if len(part) <= 5 else 0.88
            matched, best_word, score = token_word_match(part, text_upper, threshold)
            if matched:
                token_hits.append((part, best_word, score))
            else:
                token_misses.append(part)

    match_ratio = len(token_hits) / total if total > 0 else 0.0

    # ── Scoring based on token match results ─────────────────────────────────
    if is_short_single_token:
        # Short single-token: must be exact — no fuzzy fallback
        if token_hits:
            positives.append(f"Candidate name '{candidate_name}' found in document — identity confirmed")
            score_adjustment = 12
        elif found_names:
            # Document has detectable names but candidate's short name isn't among them
            if any(normalize_name_text(fn) == candidate_upper for fn in found_names):
                positives.append(f"Candidate name '{candidate_name}' matches document — identity confirmed")
                score_adjustment = 15
            else:
                issues.append(
                    f"IDENTITY MISMATCH: Candidate '{candidate_name}' not found. "
                    f"Document name(s) detected: {', '.join(found_names)}"
                )
                score_adjustment = -70
        else:
            # No names extractable and short name not found as a word
            issues.append(
                f"IDENTITY MISMATCH: Name '{candidate_name}' not found in document — "
                f"this document likely belongs to a different person"
            )
            score_adjustment = -70

    elif match_ratio >= 0.9:
        positives.append(
            f"Candidate name '{candidate_name}' fuzzy-matches OCR text — identity likely confirmed"
        )
        score_adjustment = 10

    elif match_ratio >= 0.6:
        positives.append(f"Partial name match ({len(token_hits)}/{total} parts matched)")
        score_adjustment = -5

    elif found_names:
        if any(normalize_name_text(fn) == candidate_upper for fn in found_names):
            positives.append(f"Candidate name '{candidate_name}' matches document — identity confirmed")
            score_adjustment = 15
        else:
            issues.append(
                f"IDENTITY MISMATCH: Candidate '{candidate_name}' not found. "
                f"Document name(s) detected: {', '.join(found_names)}"
            )
            score_adjustment = -70

    elif match_ratio > 0:
        issues.append(f"Only {len(token_hits)}/{total} name parts found — document may belong to someone else")
        score_adjustment = -40

    else:
        issues.append(
            f"IDENTITY MISMATCH: Name '{candidate_name}' not found in document — "
            f"this document likely belongs to a different person"
        )
        score_adjustment = -70

    return issues, positives, score_adjustment, found_names


def detect_institution(text):
    text_upper  = text.upper()
    found       = []
    category_found = None

    for category, keywords in RWANDA_INSTITUTIONS.items():
        for kw in keywords:
            pattern = r'\b' + re.escape(kw).replace(r'\ ', r'\s+') + r'\b'
            if len(kw) > 2 and re.search(pattern, text_upper):
                found.append(kw)
                category_found = category

    for code in INSTITUTION_SHORT_CODES:
        pattern = r'\b' + re.escape(code) + r'\b'
        if re.search(pattern, text_upper):
            if code not in found:
                found.append(code)
            if code in ['RP', 'IPRC', 'WDA', 'VTC']:
                category_found = category_found or 'polytechnics'
            elif code in ['UR', 'ULK', 'MKU', 'UTAB', 'AUCA', 'INES', 'ALU', 'ISAE']:
                category_found = category_found or 'universities'
            elif code in ['REB', 'NIDA', 'HEC']:
                category_found = category_found or 'government'

    if not found:
        for frag in INSTITUTION_FRAGMENTS:
            if frag in text_upper:
                found.append(frag)
                if any(p in frag for p in ['POLYTECHNIC', 'POLYTEC', 'IPRC', 'WDA']):
                    category_found = 'polytechnics'
                elif any(u in frag for u in ['UNIV', 'ULK', 'AUCA', 'INES', 'ALU', 'CMU', 'MKU', 'UTAB']):
                    category_found = 'universities'
                elif any(g in frag for g in ['NIDA', 'REB', 'HEC', 'MINEDUC']):
                    category_found = 'government'

    if 'RP.AC.RW' in text_upper or 'GRADUATE.RP' in text_upper:
        if 'RWANDA POLYTECHNIC (via URL)' not in found:
            found.append('RWANDA POLYTECHNIC (via URL)')
        category_found = 'polytechnics'
    if 'UR.AC.RW' in text_upper:
        if 'UNIVERSITY OF RWANDA (via URL)' not in found:
            found.append('UNIVERSITY OF RWANDA (via URL)')
        category_found = 'universities'

    priority = [
        'RWANDA POLYTECHNIC (via URL)', 'RWANDA POLYTECHNIC',
        'UNIVERSITY OF RWANDA (via URL)', 'UNIVERSITY OF RWANDA',
        'RP', 'UR', 'POLYTECHNIC',
    ]
    found_unique = list(dict.fromkeys(found))
    found_unique.sort(key=lambda item: priority.index(item) if item in priority else len(priority))

    return found_unique, category_found


def detect_auth_signature(text):
    text_upper = text.upper()
    for kw in AUTH_KEYWORDS:
        if kw in text_upper:
            return True, kw.title()
    for p in ['CHANCELLOR', 'RECTOR', 'REGISTRAR', 'CHARGE OF ACAD']:
        if p in text_upper:
            return True, p.title()
    return False, None


def detect_doc_type(text):
    text_upper = text.upper()

    def keyword_hits(keywords):
        hits = []
        for kw in keywords:
            pattern = r'\b' + re.escape(kw).replace(r'\ ', r'\s+') + r'\b'
            if re.search(pattern, text_upper):
                hits.append(kw)
        return hits

    id_hits    = keyword_hits(RWANDA_ID_KEYWORDS)
    cert_hits  = keyword_hits(RWANDA_CERT_KEYWORDS)
    trans_hits = keyword_hits(RWANDA_TRANSCRIPT_KEYWORDS)

    strong_id_hits = [kw for kw in id_hits if kw not in {'RWANDA', 'REPUBLIC OF RWANDA'}]
    certificate_evidence = [
        'SATISFIED THE REQUIREMENTS', 'REQUIREMENTS FOR THE AWARD',
        'ADVANCED DIPLOMA', 'SECOND CLASS', 'CONGREGATION',
        'TWO THOUSAND', 'GRADUATE.RP', 'RP.AC.RW', 'RWANDA POLYTECHNIC',
    ]
    cert_fragment_score = sum(1 for frag in certificate_evidence if frag in text_upper)

    id_score    = len(id_hits)
    cert_score  = len(cert_hits) + cert_fragment_score
    trans_score = len(trans_hits)

    if cert_score >= 2 and cert_score >= len(strong_id_hits):
        return 'certificate', cert_score
    if trans_score >= 2 and trans_score >= cert_score:
        return 'transcript', trans_score
    if len(strong_id_hits) >= 2:
        return 'national_id', id_score
    return 'unknown', 0


def validate_rwanda_id(text):
    issues, positives = [], []
    score = 100
    text_upper = text.upper()

    if re.findall(r'\b\d{16}\b', text):
        positives.append("Valid 16-digit Rwandan NID number detected")
    elif re.findall(r'\b\d{10}\b', text):
        positives.append("ID number detected (older format)")
    else:
        issues.append("No valid Rwandan NID number format found")
        score -= 20

    kw_found = [kw for kw in RWANDA_ID_KEYWORDS if kw in text_upper]
    if len(kw_found) >= 3:
        positives.append(f"Official ID keywords: {', '.join(kw_found[:3])}")
    elif len(kw_found) >= 1:
        positives.append("Some ID keywords detected")
        score -= 10
    else:
        issues.append("No official Rwandan ID keywords found")
        score -= 30

    if re.findall(r'\d{2}[./\-]\d{2}[./\-]\d{4}|\d{4}[./\-]\d{2}[./\-]\d{2}', text):
        positives.append("Date of birth field detected")
    else:
        issues.append("No date of birth detected")
        score -= 10

    inst_found, _ = detect_institution(text)
    if inst_found:
        positives.append(f"Issuing authority recognized: {', '.join(inst_found[:2])}")

    return issues, positives, max(0, score)


def validate_certificate(text):
    issues, positives = [], []
    score = 100
    text_upper = text.upper()

    inst_found, inst_category = detect_institution(text)
    if inst_found:
        positives.append(f"Recognized Rwandan institution: {', '.join(inst_found[:2])}")
        score += 5
    else:
        issues.append("Issuing institution not clearly detected — manual review recommended")
        score -= 10

    kw_found = [kw for kw in RWANDA_CERT_KEYWORDS if kw in text_upper]
    if len(kw_found) >= 4:
        positives.append("Strong certificate content verified")
    elif len(kw_found) >= 2:
        positives.append("Certificate keywords found")
        score -= 5
    else:
        issues.append("Too few certificate keywords found")
        score -= 15

    auth_found, auth_name = detect_auth_signature(text)
    if auth_found:
        positives.append(f"Issuing authority detected: {auth_name}")
    else:
        issues.append("No issuing authority signature role detected")
        score -= 8

    years = re.findall(r'\b(19|20)\d{2}\b', text)
    if years:
        positives.append(f"Issue year detected: {years[-1]}")
    else:
        if any(w in text_upper for w in ['TWO THOUSAND', 'NINETEEN', 'TWENTY']):
            positives.append("Issue year detected (written in words)")
        else:
            issues.append("No issue year found on certificate")
            score -= 8

    if re.search(r'[A-Z]{2,}\s+[A-Z]{2,}', text_upper):
        positives.append("Candidate name format detected on certificate")

    if any(url in text_upper for url in ['RP.AC.RW', 'UR.AC.RW', 'GRADUATE.RP']):
        positives.append("Official institution URL detected on certificate")
        score += 5

    if score < 60 and not inst_found:
        issues.append("Certificate lacks key verification markers — manual review recommended")

    return issues, positives, min(100, max(0, score))


def validate_transcript(text):
    issues, positives = [], []
    score = 100
    text_upper = text.upper()

    inst_found, _ = detect_institution(text)
    if inst_found:
        positives.append(f"Recognized institution: {', '.join(inst_found[:2])}")
    else:
        issues.append("Institution not recognized in Rwanda database")
        score -= 15

    kw_found = [kw for kw in RWANDA_TRANSCRIPT_KEYWORDS if kw in text_upper]
    if len(kw_found) >= 3:
        positives.append("Transcript content verified")
    elif len(kw_found) >= 1:
        positives.append("Some transcript keywords found")
        score -= 10
    else:
        issues.append("No transcript keywords detected")
        score -= 20

    if re.findall(r'\b\d{1,3}\.\d{1,2}\b|\b\d{1,3}%', text):
        positives.append("Grade values detected")
    else:
        issues.append("No grade values found in transcript")
        score -= 10

    return issues, positives, max(0, score)


def preprocess_for_ocr(img_cv):
    """Apply multiple preprocessing strategies and return the best text."""
    h, w = img_cv.shape[:2]
    results = []

    if w < 1000:
        img_cv = cv2.resize(img_cv, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    try:
        clahe     = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced  = clahe.apply(gray)
        text      = pytesseract.image_to_string(Image.fromarray(enhanced), config='--oem 3 --psm 6')
        results.append(text)
    except Exception:
        pass

    try:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text      = pytesseract.image_to_string(Image.fromarray(binary), config='--oem 3 --psm 6')
        results.append(text)
    except Exception:
        pass

    try:
        adaptive  = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        text      = pytesseract.image_to_string(Image.fromarray(adaptive), config='--oem 3 --psm 6')
        results.append(text)
    except Exception:
        pass

    try:
        img_pil   = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        img_pil   = ImageEnhance.Contrast(img_pil).enhance(2.5)
        img_pil   = ImageEnhance.Sharpness(img_pil).enhance(2.0)
        img_pil   = img_pil.convert('L')
        text      = pytesseract.image_to_string(img_pil, config='--oem 3 --psm 6')
        results.append(text)
    except Exception:
        pass

    if results:
        return max(results, key=lambda t: len(t.strip()))
    return ''


def extract_text(image_path, candidate_name=""):
    try:
        if not os.path.exists(image_path):
            return {"success": False, "error": "File not found", "text": ""}

        img_cv  = cv2.imread(image_path)
        img_pil = Image.open(image_path)

        text = preprocess_for_ocr(img_cv)

        if not text or len(text.strip()) < 10:
            text = pytesseract.image_to_string(img_pil)

        text       = text.strip()
        word_count = len(text.split())
        doc_type, keyword_score = detect_doc_type(text)
        inst_found, inst_category = detect_institution(text)

        doc_issues, doc_positives, content_score = [], [], 70

        if doc_type == 'national_id':
            doc_issues, doc_positives, content_score = validate_rwanda_id(text)
        elif doc_type == 'certificate':
            doc_issues, doc_positives, content_score = validate_certificate(text)
        elif doc_type == 'transcript':
            doc_issues, doc_positives, content_score = validate_transcript(text)
        else:
            if word_count < 10:
                doc_issues.append("Very little text extracted — image quality may be too low")
                content_score = 40
            elif word_count < 30:
                doc_issues.append("Limited text extracted — document type unconfirmed")
                content_score = 60
            else:
                doc_positives.append("Text extracted successfully")
                content_score = 75

        name_issues, name_positives, name_adjustment, found_names = match_candidate_name(
            text, candidate_name
        )
        doc_issues.extend(name_issues)
        doc_positives.extend(name_positives)
        content_score = min(100, max(0, content_score + name_adjustment))

        if name_adjustment <= -50:
            content_score = min(content_score, 35)

        has_recognized_institution = len(inst_found) > 0

        return {
            "success":                   True,
            "error":                     "",
            "text":                      text,
            "word_count":                word_count,
            "detected_type":             doc_type,
            "keyword_score":             keyword_score,
            "content_score":             content_score,
            "doc_issues":                doc_issues,
            "doc_positives":             doc_positives,
            "institutions_found":        inst_found,
            "institution_category":      inst_category,
            "institution_name":          inst_found[0] if inst_found else "",
            "has_recognized_institution": has_recognized_institution,
            "name_match_adjustment":     name_adjustment,
            "found_names":               found_names,
            "ocr_name_match":            name_adjustment >= 10,
            "ocr_name_mismatch":         name_adjustment <= -50,
        }

    except Exception as e:
        return {
            "success": False, "error": str(e), "text": "",
            "content_score": 50, "doc_issues": [], "doc_positives": [],
            "detected_type": "unknown", "institutions_found": [],
            "institution_name": "",
            "has_recognized_institution": False,
            "name_match_adjustment": 0,
            "found_names": [],
            "ocr_name_match": False,
            "ocr_name_mismatch": False,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No file path", "text": ""}))
    else:
        image_path     = sys.argv[1]
        candidate_name = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(extract_text(image_path, candidate_name)))