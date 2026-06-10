import sys
import re
import json

# ─────────────────────────────────────────────────────────────
#  hash_check.py  —  Format & number validation for Rwandan
#  documents (NIDA / NESA / UR / ULK / MKU / UTAB)
#
#  Usage:
#    python hash_check.py "<ocr_text>" "<institution>" "<doc_type>"
#
#  Returns JSON with keys:
#    checked, institution, doc_type,
#    number_found, number_value, format_valid,
#    format_detail, score_adjustment,
#    issues, positives
# ─────────────────────────────────────────────────────────────


# ── Rwanda National ID (NIDA) ─────────────────────────────────
# Format: 16 digits  e.g. 1199880012345678
# Structure:
#   digit 1   : 1 = born in Rwanda, 2 = foreign national
#   digits 2-5: birth year  (e.g. 1998)
#   digit 6   : gender (7 or 8 in older system; newer = any)
#   digits 7-16: sequence + check digit
NIDA_PATTERN = re.compile(r'\b([12]\d{15})\b')

def validate_nida_number(number):
    """Validate Rwandan NID number structure."""
    issues = []
    positives = []

    if len(number) != 16:
        return False, ["NID number is not 16 digits"], []

    first_digit = number[0]
    if first_digit not in ('1', '2'):
        issues.append(f"NID first digit '{first_digit}' invalid — must be 1 (Rwandan) or 2 (foreign)")
        return False, issues, positives

    birth_year = int(number[1:5])
    current_year = 2026
    if not (1900 <= birth_year <= current_year):
        issues.append(f"NID birth year '{birth_year}' out of valid range (1900–{current_year})")
        return False, issues, positives

    # Age sanity check — must be at least 16 to have a NID
    age = current_year - birth_year
    if age < 16:
        issues.append(f"NID birth year implies age {age} — too young for a national ID")
        return False, issues, positives

    positives.append(f"NID structure valid: {'Rwandan citizen' if first_digit == '1' else 'Foreign national'}, born {birth_year}")
    return True, issues, positives


def check_nida(text):
    """Extract and validate Rwanda National ID number."""
    matches = NIDA_PATTERN.findall(text)

    if not matches:
        # Try relaxed: any 16-digit run
        relaxed = re.findall(r'\b\d{16}\b', text)
        if relaxed:
            matches = relaxed

    if not matches:
        return {
            "number_found": False,
            "number_value": None,
            "format_valid": False,
            "format_detail": "NID number not readable — OCR quality too low (laminated card)",
            "score_adjustment": 0,   # no penalty — OCR failure on ID cards is expected
            "issues": [],            # don't penalise, model already confirmed it's a real NID
            "positives": ["Document confirmed as National ID by AI model — NID number not OCR-readable (normal for laminated cards)"]
        }

    number = matches[0]
    valid, issues, positives = validate_nida_number(number)

    if valid:
        return {
            "number_found": True,
            "number_value": number,
            "format_valid": True,
            "format_detail": f"NID number {number} passed format validation",
            "score_adjustment": 10,
            "issues": issues,
            "positives": positives
        }
    else:
        return {
            "number_found": True,
            "number_value": number,
            "format_valid": False,
            "format_detail": f"NID number {number} failed format check",
            "score_adjustment": -20,
            "issues": issues,
            "positives": positives
        }


# ── NESA (National Examinations & School Inspectorate Authority) ──
# Certificate serial number format varies by year:
#   Modern:   NESA/YYYY/NNNNNN  or  REB/YYYY/NNNNNN
#   Older:    S6/YYYY/NNNNN
#   Plain:    8–12 digit numeric code
NESA_PATTERNS = [
    re.compile(r'\b(?:NESA|REB)[/\-_]?(20\d{2})[/\-_]?(\d{4,8})\b', re.IGNORECASE),
    re.compile(r'\bS6[/\-_]?(20\d{2})[/\-_]?(\d{4,6})\b', re.IGNORECASE),
    re.compile(r'\b(?:CERT(?:IFICATE)?|SERIAL|NO|NUMBER)[:\s#]*([A-Z0-9]{6,14})\b', re.IGNORECASE),
    re.compile(r'\b(\d{8,12})\b'),   # plain numeric fallback
]

def check_nesa(text):
    """Extract and validate NESA certificate number."""
    text_upper = text.upper()

    # Try structured patterns first
    for i, pattern in enumerate(NESA_PATTERNS[:2]):
        m = pattern.search(text_upper)
        if m:
            year = int(m.group(1))
            serial = m.group(2)
            if 2000 <= year <= 2026:
                return {
                    "number_found": True,
                    "number_value": m.group(0),
                    "format_valid": True,
                    "format_detail": f"NESA certificate number found: {m.group(0)} (year {year})",
                    "score_adjustment": 10,
                    "issues": [],
                    "positives": [f"NESA certificate serial number validated: {m.group(0)}"]
                }
            else:
                return {
                    "number_found": True,
                    "number_value": m.group(0),
                    "format_valid": False,
                    "format_detail": f"NESA number year {year} is out of valid range",
                    "score_adjustment": -10,
                    "issues": [f"Certificate year {year} is invalid"],
                    "positives": []
                }

    # Fallback: plain numeric code (8–12 digits)
    m = NESA_PATTERNS[3].search(text_upper)
    if m:
        return {
            "number_found": True,
            "number_value": m.group(0),
            "format_valid": True,
            "format_detail": f"Certificate number detected (numeric): {m.group(0)}",
            "score_adjustment": 5,
            "issues": [],
            "positives": [f"Certificate number detected: {m.group(0)}"]
        }

    return {
    "number_found": False,
    "number_value": None,
    "format_valid": False,
    "format_detail": "No NESA certificate number found — OCR may not have read it",
    "score_adjustment": 0,
    "issues": [],
    "positives": ["NESA certificate type confirmed by AI model"]
}


# ── University Degree Numbers (UR / ULK / MKU / UTAB) ────────
# Common patterns across Rwandan universities:
#   UR:   UR/YYYY/FACULTY/NNNNN   or   BACHELORNNNNNN
#   ULK:  ULK/YYYY/NNNNNN
#   MKU:  MKU/YYYY/NNNNNN  or  MKU-NNNNNN
#   UTAB: UTAB/YYYY/NNNNNN
#   Generic fallback: 6–12 digit number on a degree

UNIVERSITY_PATTERNS = {
    "UR": [
        re.compile(r'\bUR[/\-_]?(20\d{2})[/\-_]?[A-Z]{0,6}[/\-_]?(\d{3,8})\b', re.IGNORECASE),
        re.compile(r'\bURN?\d{5,10}\b', re.IGNORECASE),
    ],
    "ULK": [
    re.compile(r'\bULK[/\-_]?(20\d{2})[/\-_]?(\d{4,8})\b', re.IGNORECASE),
    re.compile(r'\bULK\d{4,10}\b', re.IGNORECASE),
    re.compile(r'\b[A-Z]{1,2}\d{1,2}[/\-_](20\d{2})[/\-_](\d{3,6})\b', re.IGNORECASE),
    re.compile(r'\b[A-Z]{1,2}\d{1}[\-](20\d{2})[\-]\d{3,6}\b', re.IGNORECASE),
],
    "MKU": [
        re.compile(r'\bMKU[/\-_]?(20\d{2})?[/\-_]?(\d{4,8})\b', re.IGNORECASE),
        re.compile(r'\bMKU[\-]?\d{4,10}\b', re.IGNORECASE),
    ],
    "UTAB": [
        re.compile(r'\bUTAB[/\-_]?(20\d{2})?[/\-_]?(\d{4,8})\b', re.IGNORECASE),
        re.compile(r'\bUTAB[\-]?\d{4,10}\b', re.IGNORECASE),
    ],
}

# Generic cert/degree number fallback for any university
GENERIC_DEGREE_NUMBER = re.compile(
    r'\b(?:CERT(?:IFICATE)?|DEGREE|DIPLOMA|REG(?:ISTRATION)?|REF(?:ERENCE)?|NO|NUMBER|#)[:\s#\.]*([A-Z0-9]{5,14})\b',
    re.IGNORECASE
)
GENERIC_NUMERIC = re.compile(r'\b(\d{6,12})\b')

# Which institution codes appear in text
INSTITUTION_CODE_MAP = {
    "UNIVERSITY OF RWANDA": "UR",
    "UR-": "UR",
    "KIGALI INDEPENDENT UNIVERSITY": "ULK",
    "UNIVERSITE LIBRE DE KIGALI": "ULK",
    "ULK": "ULK",
    "MOUNT KENYA UNIVERSITY": "MKU",
    "MKU": "MKU",
    "UNIVERSITY OF TECHNOLOGY AND ARTS": "UTAB",
    "UTAB": "UTAB",
}

def detect_university_code(text):
    """Detect which university is on the document."""
    text_upper = text.upper()
    for keyword, code in INSTITUTION_CODE_MAP.items():
        if keyword in text_upper:
            return code
    return None

def check_university(text):
    """Extract and validate university degree certificate number."""
    text_upper = text.upper()
    uni_code = detect_university_code(text_upper)

    # Try institution-specific patterns
    if uni_code and uni_code in UNIVERSITY_PATTERNS:
        for pattern in UNIVERSITY_PATTERNS[uni_code]:
            m = pattern.search(text_upper)
            if m:
                number = m.group(0)
                # Validate year if captured
                try:
                    year = int(m.group(1)) if m.lastindex and m.lastindex >= 1 else None
                    if year and not (1990 <= year <= 2026):
                        return {
                            "number_found": True,
                            "number_value": number,
                            "format_valid": False,
                            "format_detail": f"{uni_code} certificate year {year} is out of range",
                            "score_adjustment": -10,
                            "issues": [f"Degree year {year} is invalid for {uni_code}"],
                            "positives": []
                        }
                except (IndexError, TypeError):
                    pass

                return {
                    "number_found": True,
                    "number_value": number,
                    "format_valid": True,
                    "format_detail": f"{uni_code} certificate number found: {number}",
                    "score_adjustment": 10,
                    "issues": [],
                    "positives": [f"{uni_code} degree certificate number validated: {number}"]
                }

    # Generic fallback — any degree/cert number label
    m = GENERIC_DEGREE_NUMBER.search(text_upper)
    if m:
        number = m.group(1)
        label = "University" if not uni_code else uni_code
        return {
            "number_found": True,
            "number_value": number,
            "format_valid": True,
            "format_detail": f"Certificate/degree reference number detected: {number}",
            "score_adjustment": 5,
            "issues": [],
            "positives": [f"{label} degree reference number detected: {number}"]
        }

    # Last resort: plain 6–12 digit number
    m = GENERIC_NUMERIC.search(text_upper)
    if m:
        number = m.group(1)
        return {
            "number_found": True,
            "number_value": number,
            "format_valid": True,
            "format_detail": f"Numeric reference number found: {number}",
            "score_adjustment": 3,
            "issues": [],
            "positives": [f"Numeric reference detected: {number}"]
        }

    institution_label = uni_code or "University"
    return {
        "number_found": False,
        "number_value": None,
        "format_valid": False,
        "format_detail": f"No {institution_label} certificate number found",
        "score_adjustment": -10,
        "issues": [f"No degree/certificate number detected for {institution_label}"],
        "positives": []
    }


# ── Institution router ────────────────────────────────────────
def detect_institution_type(text, institution_hint=""):
    """Decide which validator to use based on OCR text + hint."""
    text_upper = text.upper()
    hint = institution_hint.upper()

    # National ID signals
    nida_signals = [
        'INDANGAMUNTU', 'NATIONAL ID', 'NID', 'NIDA',
        'DATE OF BIRTH', 'ITARIKI', 'UBWENEGIHUGU',
        'NATIONAL IDENTIFICATION'
    ]
    if any(s in text_upper for s in nida_signals) or 'NATIONAL_ID' in hint or 'NID' in hint:
        return 'nida'

    # NESA signals
    nesa_signals = [
        'NESA', 'NATIONAL EXAMINATION', 'RWANDA EDUCATION BOARD',
        'REB', 'SENIOR SIX', 'S6', 'SECONDARY', 'UACE', 'UCE',
        'ADVANCED LEVEL', 'ORDINARY LEVEL'
    ]
    if any(s in text_upper for s in nesa_signals) or 'NESA' in hint or 'REB' in hint:
        return 'nesa'

    # University signals
    uni_signals = [
        'UNIVERSITY OF RWANDA', 'KIGALI INDEPENDENT UNIVERSITY',
        'UNIVERSITE LIBRE DE KIGALI', 'MOUNT KENYA UNIVERSITY',
        'UNIVERSITY OF TECHNOLOGY AND ARTS',
        'ULK', 'MKU', 'UTAB',
    ]
    # UR needs careful match to avoid false positive with "RP"
    if re.search(r'\bUR\b', text_upper) or any(s in text_upper for s in uni_signals):
        return 'university'

    return None


# ── Main entry point ──────────────────────────────────────────
def run_hash_check(ocr_text, institution_hint="", doc_type_hint=""):
    """
    Main function called from run_verify.py.
    Returns a dict with validation results.
    """
    ocr_text = ocr_text or ""

    # ── Direct doc_type routing (most reliable — from DB, not OCR) ──
    doc_type_lower = (doc_type_hint or institution_hint or "").lower().strip()

    if doc_type_lower == "national_id":
        inst_type = "nida"
    elif doc_type_lower in ("nesa", "secondary", "reb"):
        inst_type = "nesa"
    elif doc_type_lower in ("certificate", "transcript", "degree"):
        # Need OCR text to distinguish university from RP/NESA
        # RP uses QR so skip if OCR text is too poor to read
        inst_type = detect_institution_type(ocr_text, institution_hint)
        # If OCR too poor to detect university, skip gracefully
        if inst_type not in ("nesa", "university"):
            inst_type = None
    else:
        # Fallback to OCR-based detection
        if not ocr_text or len(ocr_text.strip()) < 10:
            return {
                "checked": False,
                "institution": None,
                "doc_type": None,
                "number_found": False,
                "number_value": None,
                "format_valid": False,
                "format_detail": "No OCR text and no doc_type hint provided",
                "score_adjustment": 0,
                "issues": [],
                "positives": []
            }
        inst_type = detect_institution_type(ocr_text, institution_hint)

    if inst_type == 'nida':
        result = check_nida(ocr_text)
        result['institution'] = 'Rwanda National ID (NIDA)'
        result['doc_type'] = 'national_id'

    elif inst_type == 'nesa':
        result = check_nesa(ocr_text)
        result['institution'] = 'NESA / Rwanda Education Board'
        result['doc_type'] = 'certificate'

    elif inst_type == 'university':
        uni_code = detect_university_code(ocr_text)
        result = check_university(ocr_text)
        result['institution'] = uni_code or 'University (Rwanda)'
        result['doc_type'] = 'certificate'

    else:
        # Not a supported institution for hash check
        return {
            "checked": False,
            "institution": None,
            "doc_type": doc_type_hint or None,
            "number_found": False,
            "number_value": None,
            "format_valid": False,
            "format_detail": "Institution not in hash-check scope (RP uses QR instead)",
            "score_adjustment": 0,
            "issues": [],
            "positives": []
        }

    result['checked'] = True
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "checked": False, "error": "Usage: hash_check.py <ocr_text> [institution] [doc_type]"
        }))
        sys.exit(1)

    ocr_text         = sys.argv[1]
    institution_hint = sys.argv[2] if len(sys.argv) > 2 else ""
    doc_type_hint    = sys.argv[3] if len(sys.argv) > 3 else ""

    output = run_hash_check(ocr_text, institution_hint, doc_type_hint)
    print(json.dumps(output))