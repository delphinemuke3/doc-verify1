import sys
import json
import os
import re
from datetime import datetime

# ── Software red flags — editing tools that indicate tampering ────────────────
EDITING_SOFTWARE_REDFLAGS = [
    'adobe photoshop', 'photoshop', 'gimp', 'paint.net', 'inkscape',
    'canva', 'pixlr', 'fotor', 'befunky', 'picsart', 'snapseed',
    'lightroom', 'affinity photo', 'corel', 'paintshop',
    'microsoft paint', 'ms paint', 'paint 3d',
    'online image editor', 'iloveimg', 'remove.bg',
    'img2go', 'lunapic', 'picmonkey', 'fotojet',
]

# ── Software that is expected/legitimate for scanned documents ────────────────
LEGITIMATE_SOFTWARE = [
    'scanner', 'scan', 'epson', 'canon', 'hp', 'fujitsu', 'brother',
    'nikon', 'samsung', 'xerox', 'ricoh', 'konica', 'sharp',
    'iphone', 'android', 'samsung camera', 'pixel',
    'adobe acrobat', 'acrobat', 'pdf',
    'microsoft office', 'word',
    'windows camera', 'camera',
    'camscanner', 'adobe scan', 'microsoft lens', 'genius scan',
    'turboscan', 'scanbot', 'tiny scanner',
]


def get_exif_data(image_path):
    """Extract EXIF data using Pillow."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img  = Image.open(image_path)
        exif = img._getexif()

        if not exif:
            return {}

        result = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            try:
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='ignore').strip()
                result[str(tag)] = str(value)[:300]
            except:
                pass
        return result

    except Exception:
        return {}


def get_file_metadata(image_path):
    """Get basic file system metadata."""
    try:
        stat     = os.stat(image_path)
        created  = datetime.fromtimestamp(stat.st_ctime)
        modified = datetime.fromtimestamp(stat.st_mtime)
        size_kb  = stat.st_size / 1024

        return {
            'file_size_kb':   round(size_kb, 1),
            'created':        created.strftime('%Y-%m-%d %H:%M:%S'),
            'modified':       modified.strftime('%Y-%m-%d %H:%M:%S'),
            'extension':      os.path.splitext(image_path)[1].lower(),
        }
    except Exception as e:
        return {'error': str(e)}


def check_software(software_str):
    """
    Check if software used is legitimate or suspicious.
    Returns: 'editing', 'legitimate', 'scanner_app', or 'unknown'
    """
    if not software_str:
        return 'unknown', None

    sw_lower = software_str.lower().strip()

    for sw in EDITING_SOFTWARE_REDFLAGS:
        if sw in sw_lower:
            return 'editing', software_str

    for sw in LEGITIMATE_SOFTWARE:
        if sw in sw_lower:
            if any(s in sw_lower for s in ['scanner', 'scan', 'epson', 'canon', 'hp',
                                            'fujitsu', 'brother', 'xerox', 'ricoh']):
                return 'scanner', software_str
            return 'legitimate', software_str

    return 'unknown', software_str


def analyze_dates(exif_data, file_meta):
    """
    Analyze date consistency.
    Flags if modification date is much newer than creation date,
    or if dates are suspicious.
    """
    issues    = []
    positives = []

    # EXIF dates
    datetime_original  = exif_data.get('DateTimeOriginal', '')
    datetime_digitized = exif_data.get('DateTimeDigitized', '')
    datetime_modified  = exif_data.get('DateTime', '')

    # Check for future dates
    now = datetime.now()
    for label, date_str in [
        ('Original', datetime_original),
        ('Digitized', datetime_digitized),
        ('Modified', datetime_modified)
    ]:
        if date_str:
            try:
                dt = datetime.strptime(date_str[:19], '%Y:%m:%d %H:%M:%S')
                if dt > now:
                    issues.append(f'EXIF {label} date is in the future: {date_str} — possible manipulation')
                elif dt.year < 1990:
                    issues.append(f'EXIF {label} date is suspiciously old: {date_str}')
            except:
                pass

    # Check file modification vs creation
    if file_meta.get('created') and file_meta.get('modified'):
        try:
            created  = datetime.strptime(file_meta['created'],  '%Y-%m-%d %H:%M:%S')
            modified = datetime.strptime(file_meta['modified'], '%Y-%m-%d %H:%M:%S')
            diff_days = (modified - created).days
            if diff_days > 30:
                issues.append(
                    f'File was modified {diff_days} days after creation — '
                    'possible post-scan editing'
                )
            elif diff_days >= 0:
                positives.append('File creation and modification dates are consistent')
        except:
            pass

    return issues, positives


def check_metadata(image_path):
    try:
        if not os.path.exists(image_path):
            return {
                "success": False, "error": "File not found",
                "issues": [], "positives": [], "score": 70,
                "software_detected": None, "software_suspicious": False
            }

        ext = os.path.splitext(image_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp']:
            return {
                "success": True, "score": 70,
                "issues": [], "positives": ["File format does not support EXIF metadata"],
                "software_detected": None, "software_suspicious": False
            }

        issues    = []
        positives = []
        score     = 100
        deductions = []

        # ── Get metadata ──────────────────────────────────────────────────────
        exif_data = get_exif_data(image_path)
        file_meta = get_file_metadata(image_path)

        # ── Software check ────────────────────────────────────────────────────
        software_raw  = (
            exif_data.get('Software', '') or
            exif_data.get('ProcessingSoftware', '') or
            exif_data.get('HostComputer', '')
        )
        sw_type, sw_name = check_software(software_raw)
        software_suspicious = False

        if sw_type == 'editing':
            software_suspicious = True
            issues.append(
                f'⚠ EDITING SOFTWARE DETECTED: "{sw_name}" — '
                'document was processed with image editing software. '
                'This is a strong indicator of tampering.'
            )
            deductions.append(40)

        elif sw_type == 'scanner':
            positives.append(f'Document scanned with legitimate scanner software: {sw_name}')

        elif sw_type == 'legitimate':
            positives.append(f'Software consistent with legitimate document capture: {sw_name}')

        elif sw_type == 'unknown' and software_raw:
            # Unknown software — mild warning
            issues.append(f'Unknown software detected: "{software_raw}" — manual check recommended')
            deductions.append(5)

        # ── Camera/device info ────────────────────────────────────────────────
        make  = exif_data.get('Make', '')
        model = exif_data.get('Model', '')
        if make or model:
            device = f"{make} {model}".strip()
            positives.append(f'Captured with device: {device}')

        # ── GPS data check ────────────────────────────────────────────────────
        # GPS in a scanned certificate is suspicious
        gps_info = exif_data.get('GPSInfo', '')
        if gps_info:
            issues.append(
                'GPS coordinates embedded in document image — '
                'scanned certificates should not have GPS data'
            )
            deductions.append(5)

        # ── Date consistency ──────────────────────────────────────────────────
        date_issues, date_positives = analyze_dates(exif_data, file_meta)
        issues    += date_issues
        positives += date_positives

        # ── EXIF presence check ───────────────────────────────────────────────
        if not exif_data:
            # No EXIF — could mean it was stripped (common when editing online)
            issues.append(
                'No EXIF metadata found — metadata may have been stripped. '
                'Online editing tools often remove EXIF data.'
            )
            deductions.append(10)
        else:
            positives.append(f'EXIF metadata present ({len(exif_data)} fields)')

        # ── File size sanity ──────────────────────────────────────────────────
        size_kb = file_meta.get('file_size_kb', 0)
        if size_kb < 10:
            issues.append(f'File size very small ({size_kb}KB) — may be a low-quality copy')
            deductions.append(10)
        elif size_kb > 100:
            positives.append(f'File size consistent with a real scan ({size_kb}KB)')

        # ── Color space check ─────────────────────────────────────────────────
        color_space = exif_data.get('ColorSpace', '')
        if color_space == '65535':
            issues.append('Unusual color space detected — may indicate processing')
            deductions.append(5)

        # ── Final score ───────────────────────────────────────────────────────
        total_deduction = sum(deductions)
        score = max(0, min(100, 100 - total_deduction))

        # Key fields to return
        key_exif = {}
        for field in ['Software', 'Make', 'Model', 'DateTimeOriginal',
                      'DateTimeDigitized', 'DateTime', 'ProcessingSoftware']:
            if field in exif_data:
                key_exif[field] = exif_data[field]

        return {
            "success":              True,
            "score":                score,
            "software_detected":    sw_name or None,
            "software_type":        sw_type,
            "software_suspicious":  software_suspicious,
            "file_size_kb":         file_meta.get('file_size_kb'),
            "file_created":         file_meta.get('created'),
            "file_modified":        file_meta.get('modified'),
            "exif_fields_found":    len(exif_data),
            "key_exif":             key_exif,
            "issues":               issues,
            "positives":            positives,
            "score_adjustment":     -total_deduction
        }

    except Exception as e:
        return {
            "success": False, "error": str(e),
            "score": 70, "issues": [], "positives": [],
            "software_detected": None, "software_suspicious": False
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: metadata_check.py <image_path>"
        }))
        sys.exit(1)

    result = check_metadata(sys.argv[1])
    print(json.dumps(result, indent=2))