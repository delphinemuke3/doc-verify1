import sys
import os
import json
import subprocess


MIN_VALID_CONFIDENCE = 60

# Must match CLASS_MIN_CONFIDENCE in config.php
CLASS_MIN_CONFIDENCE_OVERRIDE = {
    "Rwanda Driving License": 30,
    "Rwanda National ID":     40,
    "NESA Certificate":       40,
    "RP Degree":              40,
    "RP Transcript":          40,
    "ULK Degree":             40,
    "ULK Transcript":         40,
    "UR Degree":              40,
    "UR Transcript":          40,
    "MKU Transcript":         40,
    "UTAB Degree":            40,
    "MKU Degree":             40,
    "UTAB Transcript":        40,
}


def expected_model_type(doc_type):
    mapping = {
        "national_id":     {"id"},
        "driving_license": {"license"},
        "certificate":     {"certificate", "degree"},
        "transcript":      {"transcript"},
    }
    return mapping.get(doc_type)


def run_script(script, args=None):
    py  = sys.executable
    cmd = [py, script] + (args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {"success": False, "error": result.stderr.strip() or "No output"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_log(message):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(base_dir, 'python', 'run_verify.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(message.rstrip() + '\n')
    except Exception:
        pass


def convert_pdf(pdf_path, py_dir):
    try:
        result = run_script(os.path.join(py_dir, 'pdf_convert.py'), [pdf_path])
        if result.get('success') and result.get('image_path'):
            img_path = result['image_path']
            if not os.path.isabs(img_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                img_path = os.path.join(base_dir, img_path)
            if os.path.exists(img_path):
                return img_path
        return None
    except Exception as e:
        write_log(f"[PDF_CONVERT] Error: {e}")
        return None


# ── Classes that support OCR name verification ────────────────────────────────
# RP and UTAB use QR online verification for name matching — OCR is unreliable
# on those layouts (body text like "ADVANCED DIPLOMA IN INFORMATION..." gets
# mistaken for the candidate name). UR and ULK have no online portal so OCR
# is the only name-check available for them.
OCR_SUPPORTED_CLASSES = {
    "UR Degree",
    "UR Transcript",
    "ULK Degree",
    "ULK Transcript",
}


def main():
    if len(sys.argv) < 4:
        print("Usage: run_verify.py <doc_id> <candidate_id> <candidate_name> [confidence]")
        return

    doc_id         = sys.argv[1]
    candidate_id   = None if sys.argv[2] in ("", "0", "null", "None") else sys.argv[2]
    candidate_name = sys.argv[3] if len(sys.argv) > 3 else ""

    raw_conf   = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
    detect_conf_pct = int(raw_conf * 100) if raw_conf <= 1.0 else int(raw_conf)

    db_driver = None
    db_module = None
    try:
        import pymysql
        db_module = pymysql
        db_driver = 'pymysql'
    except ImportError:
        try:
            import mysql.connector
            db_module = mysql.connector
            db_driver = 'mysql.connector'
        except ImportError:
            pass

    if db_module is None:
        msg = 'Error: missing Python MySQL driver.'
        write_log(msg)
        print(msg)
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_dir   = os.path.join(base_dir, 'python')

    config = {'host': 'localhost', 'user': 'root', 'passwd': '', 'db': 'doc_verify_db'}
    if db_driver == 'mysql.connector':
        config['password'] = config.pop('passwd')
        config['database'] = config.pop('db')

    try:
        conn = db_module.connect(**config)
        cur  = conn.cursor()

        cur.execute("SELECT file_path, doc_type FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            print("Document not found")
            return

        file_path           = os.path.join(base_dir, doc[0])
        selected_doc_type   = doc[1]
        allowed_model_types = expected_model_type(selected_doc_type)
        is_pdf              = file_path.lower().endswith('.pdf')
        all_issues          = []
        all_positives       = []
        pdf_converted       = False

        qr_result = {
            "success": False, "qr_found": False, "trusted": False,
            "verified_online": False, "name_match": None,
            "institution": None, "qr_url": None, "qr_data": None,
            "online_status": "", "issues": [], "positives": []
        }
        metadata_result = {
            "success": False, "score": 70, "software_detected": None,
            "software_suspicious": False, "issues": [], "positives": []
        }
        dup_result = {
            "checked": False, "duplicate_found": False,
            "score_adjustment": 0, "issues": [], "positives": [],
            "other_candidate": None
        }
        ocr_result = {
            "success": False, "ocr_name_match": False,
            "ocr_name_mismatch": False, "found_names": []
        }

        verify_path = file_path
        if is_pdf:
            write_log(f"[PDF] Attempting to convert PDF: {file_path}")
            converted_image = convert_pdf(file_path, py_dir)

            if converted_image:
                write_log(f"[PDF] Converted to image: {converted_image}")
                verify_path   = converted_image
                pdf_converted = True
                is_pdf        = False
                all_positives.append(
                    "PDF automatically converted to image for AI model verification"
                )
            else:
                write_log(f"[PDF] Conversion failed — cannot verify")
                final_score = 0
                status = 'Fake'
                rec = (
                    'PDF could not be converted for verification. '
                    'Please ask the candidate to upload a JPG or PNG scan instead.'
                )
                all_issues.append('PDF conversion failed — document cannot be verified automatically.')

                issues_str = '; '.join(all_issues)
                cur.execute("SELECT id FROM verifications WHERE document_id = %s", (doc_id,))
                existing = cur.fetchone()
                if existing:
                    cur.execute(
                        "UPDATE verifications SET authenticity_score=%s, status=%s, issues=%s, recommendation=%s, verified_at=NOW() WHERE document_id=%s",
                        (final_score, status, issues_str, rec, doc_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO verifications (candidate_id, document_id, authenticity_score, status, issues, recommendation, verified_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                        (candidate_id, doc_id, final_score, status, issues_str, rec)
                    )
                conn.commit()
                cur.close()
                conn.close()
                return

        # ── Step 1: Metadata Check ────────────────────────────────────────────
        write_log(f"[METADATA] Running metadata_check.py on {verify_path}")
        metadata_result = run_script(
            os.path.join(py_dir, 'metadata_check.py'),
            [verify_path]
        ) or metadata_result
        write_log(f"[METADATA] {json.dumps(metadata_result)}")

        if metadata_result.get('metadata_suspicious'):
            all_issues    += metadata_result.get('issues', [])
            all_positives += metadata_result.get('positives', [])

        # ── Step 1b: Duplicate Detection ──────────────────────────────────────
        write_log(f"[DUPLICATE] Checking for duplicate submissions")
        dup_result = run_script(
            os.path.join(py_dir, 'duplicate_check.py'),
            [verify_path, doc_id, str(candidate_id or '0')]
        ) or dup_result
        write_log(f"[DUPLICATE] {json.dumps(dup_result)}")

        all_issues    += dup_result.get('issues', [])
        all_positives += dup_result.get('positives', [])

        # ── Step 2: YOLOv8 Detection ──────────────────────────────────────────
        # Run detection BEFORE OCR so we know the document class.
        # OCR name check is only applied to UR and ULK documents.
        write_log(f"[DETECT] Running detect.py on {verify_path} with conf={detect_conf_pct}%")
        detect = run_script(
            os.path.join(py_dir, 'detect.py'),
            [verify_path, str(detect_conf_pct)]
        ) or {"success": False, "verified": False, "detections": []}
        write_log(f"[DETECT] {json.dumps(detect)}")
        detect_verified = detect.get('verified', False)

        # Determine detected class early so OCR gate can use it
        early_detection  = (detect.get('detections') or [{}])[0]
        early_class      = early_detection.get('class', '')

        # ── Step 2b: OCR Name Check (UR and ULK only) ─────────────────────────
        # RP and UTAB use QR online verification for name matching.
        # OCR is unreliable on those layouts — it picks up course titles
        # like "ADVANCED DIPLOMA IN INFORMATION AND COMMUNICATION TECHNOLOGY"
        # instead of the candidate name, causing false mismatches.
        # Only run OCR for UR and ULK where no online portal exists.
        if candidate_name and early_class in OCR_SUPPORTED_CLASSES:
            write_log(f"[OCR] Running for {early_class} — OCR-supported class")
            ocr_result = run_script(
                os.path.join(py_dir, 'ocr_extract.py'),
                [verify_path, candidate_name]
            ) or ocr_result
            write_log(f"[OCR] mismatch={ocr_result.get('ocr_name_mismatch')} names={ocr_result.get('found_names')}")

            if ocr_result.get('ocr_name_mismatch'):
                found = [n for n in ocr_result.get('found_names', []) if len(n) > 5 and not any(c.isdigit() for c in n)]
                doc_name = found[0] if found else 'another person'
                all_issues.append(
                    f"⚠ NAME MISMATCH: Certificate shows '{doc_name}' "
                    f"but candidate is '{candidate_name}' — possible borrowed certificate!"
                )
            elif ocr_result.get('ocr_name_match'):
                all_positives.append("✔ OCR NAME CONFIRMED: Candidate name found on document")
        elif candidate_name and early_class:
            # Document class detected but OCR not applicable — log and skip silently
            write_log(f"[OCR] Skipped for {early_class} — QR verification handles name check for this class")

        # ── Step 3: QR Code Verification ──────────────────────────────────────
        write_log(f"[QR] Running qr_check.py on {verify_path}")
        qr_result = run_script(
            os.path.join(py_dir, 'qr_check.py'),
            [verify_path, candidate_name]
        ) or qr_result
        write_log(f"[QR] {json.dumps(qr_result)}")

        all_issues    += qr_result.get('issues', [])
        all_positives += qr_result.get('positives', [])

        qr_bonus = 0
        if qr_result.get('qr_found'):
            if qr_result.get('trusted') and qr_result.get('verified_online'):
                qr_bonus = 10
                all_positives.append(
                    f"QR verified online at {qr_result.get('institution', 'trusted institution')} (+10 bonus)"
                )
            elif qr_result.get('trusted'):
                qr_bonus = 5
                all_positives.append(
                    f"QR links to trusted institution: {qr_result.get('institution', '')} (+5 bonus)"
                )
            elif not qr_result.get('trusted'):
                qr_bonus = -10
                all_issues.append("QR links to unrecognized domain (-10 penalty)")

            if qr_result.get('name_match') is False:
                all_issues.append(
                    "⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!"
                )

        metadata_penalty = 0
        if metadata_result.get('software_suspicious'):
            metadata_penalty = -30
            all_issues.append(
                f"⚠ CRITICAL: Document edited with {metadata_result.get('software_detected')} — "
                "strong indicator of tampering!"
            )

        # ── Step 4: Score ─────────────────────────────────────────────────────
        if detect_verified:
            detection        = (detect.get('detections') or [{}])[0]
            detect_class     = detection.get('class') or 'trained document class'
            detect_label     = detection.get('description') or detect_class
            detected_type    = detection.get('type', 'unknown')
            model_confidence = detect.get(
                'model_confidence',
                detection.get('confidence', detect.get('score', 100))
            )
            type_matches = (
                allowed_model_types is not None
                and detected_type in allowed_model_types
            )

            min_conf = CLASS_MIN_CONFIDENCE_OVERRIDE.get(detect_class, MIN_VALID_CONFIDENCE)

            if model_confidence >= min_conf and type_matches:
                dup_penalty = dup_result.get('score_adjustment', 0)
                final_score = min(100, max(0, 100 + qr_bonus + metadata_penalty + dup_penalty))
                status = 'Verified' if final_score >= 75 else 'Suspicious'

                rec = (
                    f"Document matches trained model class: {detect_class}. "
                    f"Description: {detect_label}. "
                    f"Confidence: {model_confidence}% (required {min_conf}%). "
                    + (f"QR verified online at {qr_result.get('institution', '')}. " if qr_result.get('verified_online') else "")
                    + (f"PDF auto-converted for verification. " if pdf_converted else "")
                    + ("Marked valid at 100%. Candidate may proceed." if final_score == 100 else
                       "Some issues detected — manual review recommended.")
                )
                all_positives.append(
                    f"Trained model recognized {detect_label} ({model_confidence}% confidence, required {min_conf}%)."
                )

                if final_score >= 75 and not metadata_result.get('software_suspicious'):
                    name_issues = [i for i in all_issues if 'borrowed' in i.lower() or 'name' in i.lower() or 'CRITICAL' in i]
                    meta_issues = [i for i in all_issues if 'editing' in i.lower() or 'photoshop' in i.lower() or 'software' in i.lower()]
                    dup_issues  = [i for i in all_issues if 'duplicate' in i.lower()]
                    all_issues  = name_issues + meta_issues + dup_issues

                if qr_result.get('name_match') is False:
                    final_score = 50
                    status = 'Suspicious'
                    rec = "Document type confirmed by AI but name mismatch via QR. Manual review required."

                if ocr_result.get('ocr_name_mismatch') and qr_result.get('name_match') is not True:
                    final_score = min(final_score, 50)
                    status = 'Suspicious'
                    rec = "Document type confirmed by AI but name mismatch via OCR. Manual review required."

                if metadata_result.get('software_suspicious'):
                    final_score = min(final_score, 30)
                    status = 'Fake'
                    rec = (
                        f"Document was edited with {metadata_result.get('software_detected')}. "
                        "This is a strong indicator of tampering. Reject this document."
                    )

                if dup_result.get('duplicate_found') and not dup_result.get('same_candidate'):
                    final_score = min(final_score, 30)
                    status = 'Fake'
                    rec = (
                        f"DUPLICATE DOCUMENT: This file was previously submitted by "
                        f"'{dup_result.get('other_candidate', 'another candidate')}'. "
                        "This is a borrowed certificate. Reject this application."
                    )

            else:
                final_score = 0
                status = 'Fake'
                if not type_matches and allowed_model_types:
                    expected = ', '.join(sorted(allowed_model_types))
                    rec = (
                        f"Document type mismatch. Selected '{selected_doc_type}' "
                        f"but model detected {detect_class} ({detected_type})."
                    )
                    all_issues.append(
                        f"Type mismatch: expected {expected}, got {detect_label} ({detected_type}) at {model_confidence}%."
                    )
                else:
                    hint = detect.get('low_conf_hint', '')
                    rec = hint if hint else (
                        f"Detected '{detect_class}' at {model_confidence}% "
                        f"(required {min_conf}%). "
                        "Please upload a clear, flat, well-lit scan of the front of the document."
                    )
                    all_issues.append(
                        f"Low-confidence detection: {detect_label} ({model_confidence}%, required {min_conf}%)."
                    )
        else:
            final_score = 0
            status = 'Fake'
            rec = 'Document not recognized by trained model. Treat as fake or unsupported.'
            error = detect.get('error', '')
            issue = 'No trained model document class detected.'
            if error:
                issue += f" Error: {error}"
            all_issues.append(issue)

        issues_str  = '; '.join(all_issues)
        full_result = {
            "final_score":         final_score,
            "status":              status,
            "recommendation":      rec,
            "issues":              all_issues,
            "positives":           all_positives,
            "qr_found":            qr_result.get('qr_found', False),
            "qr_trusted":          qr_result.get('trusted', False),
            "qr_verified":         qr_result.get('verified_online', False),
            "qr_institution":      qr_result.get('institution', ''),
            "qr_url":              qr_result.get('qr_url', ''),
            "qr_data":             qr_result.get('qr_data', ''),
            "name_match":          qr_result.get('name_match'),
            "pdf_converted":       pdf_converted,
            "metadata_software":   metadata_result.get('software_detected'),
            "metadata_suspicious": metadata_result.get('software_suspicious', False),
            "duplicate_found":     dup_result.get('duplicate_found', False),
            "other_candidate":     dup_result.get('other_candidate'),
        }

        cur.execute("SELECT id FROM verifications WHERE document_id = %s", (doc_id,))
        existing = cur.fetchone()

        qr_url_val      = qr_result.get('qr_url', '') or ''
        qr_inst_val     = qr_result.get('institution', '') or ''
        qr_verified_val = 1 if qr_result.get('verified_online') else 0
        name_match_val  = 1 if qr_result.get('name_match') is True else (0 if qr_result.get('name_match') is False else None)
        cert_holder_val = qr_result.get('extracted_name', '') or ''

        if existing:
            cur.execute(
                "UPDATE verifications SET authenticity_score=%s, status=%s, issues=%s, recommendation=%s, qr_url=%s, qr_institution=%s, qr_verified=%s, name_match=%s, cert_holder=%s, verified_at=NOW() WHERE document_id=%s",
                (final_score, status, issues_str, rec, qr_url_val, qr_inst_val, qr_verified_val, name_match_val, cert_holder_val, doc_id)
            )
        else:
            cur.execute(
                "INSERT INTO verifications (candidate_id, document_id, authenticity_score, status, issues, recommendation, qr_url, qr_institution, qr_verified, name_match, cert_holder, verified_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                (candidate_id, doc_id, final_score, status, issues_str, rec, qr_url_val, qr_inst_val, qr_verified_val, name_match_val, cert_holder_val)
            )

        conn.commit()
        cur.close()
        conn.close()

        write_log(f"[DONE] Score={final_score}% | Status={status} | Conf={model_confidence if detect_verified else 0}% | Required={min_conf if detect_verified else 'N/A'} | PDF={pdf_converted}")
        print(json.dumps(full_result))

    except Exception as e:
        write_log(f"[ERROR] {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()