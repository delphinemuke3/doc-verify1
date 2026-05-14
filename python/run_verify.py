import sys
import os
import json
import subprocess


MIN_VALID_CONFIDENCE = 60


def expected_model_type(doc_type):
    mapping = {
        "national_id": {"id"},
        "driving_license": {"license"},
        "certificate": {"certificate", "degree"},
        "transcript": {"transcript"},
    }
    return mapping.get(doc_type)


def run_script(script, args=None):
    py = sys.executable
    cmd = [py, script] + (args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {
            "success": False,
            "error": result.stderr.strip() or "No output from detector"
        }
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


def main():
    if len(sys.argv) < 4:
        print("Usage: run_verify.py <doc_id> <candidate_id> <candidate_name> [confidence]")
        return

    doc_id = sys.argv[1]
    candidate_id = None if sys.argv[2] in ("", "0", "null", "None") else sys.argv[2]
    confidence = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25

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
        message = 'Error: missing Python MySQL driver. Install pymysql or mysql-connector-python.'
        write_log(message)
        print(message)
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_dir = os.path.join(base_dir, 'python')

    config = {
        'host': 'localhost',
        'user': 'root',
        'passwd': '',
        'db': 'doc_verify_db'
    }
    if db_driver == 'mysql.connector':
        config['password'] = config.pop('passwd')
        config['database'] = config.pop('db')

    try:
        conn = db_module.connect(**config)
        cur = conn.cursor()

        cur.execute(
            "SELECT file_path, doc_type FROM documents WHERE id = %s",
            (doc_id,)
        )
        doc = cur.fetchone()
        if not doc:
            print("Document not found")
            return

        file_path = os.path.join(base_dir, doc[0])
        selected_doc_type = doc[1]
        allowed_model_types = expected_model_type(selected_doc_type)
        is_pdf = file_path.lower().endswith('.pdf')
        all_issues = []
        all_positives = []

        if is_pdf:
            final_score = 0
            status = 'Fake'
            rec = 'Only JPG and PNG images can be checked by the trained model right now.'
            all_issues.append('PDF uploaded - trained model detection supports image files only.')
        else:
            detect = run_script(
                os.path.join(py_dir, 'detect.py'),
                [file_path, str(confidence)]
            )
            detect_verified = detect.get('verified', False)

            if detect_verified:
                detection = (detect.get('detections') or [{}])[0]
                detect_class = detection.get('class') or 'trained document class'
                detect_label = (
                    detection.get('description')
                    or detect_class
                )
                detected_type = detection.get('type', 'unknown')
                model_confidence = detect.get(
                    'model_confidence',
                    detection.get('confidence', detect.get('score', 100))
                )
                type_matches = (
                    allowed_model_types is not None
                    and detected_type in allowed_model_types
                )

                if model_confidence >= MIN_VALID_CONFIDENCE and type_matches:
                    final_score = 100
                    status = 'Verified'
                    rec = (
                        f"Document matches trained model class: {detect_class}. "
                        f"Description: {detect_label}. "
                        f"Confidence: {model_confidence}%. "
                        "Marked valid at 100%. Candidate may proceed."
                    )
                    all_positives.append(
                        f"Trained model recognized {detect_label} ({model_confidence}% confidence)."
                    )
                else:
                    final_score = 0
                    status = 'Fake'
                    if allowed_model_types is None:
                        rec = 'Please select the exact document type before automatic model verification.'
                        all_issues.append(
                            f"Selected document type '{selected_doc_type}' cannot be automatically verified against model class {detect_class}."
                        )
                    elif not type_matches:
                        expected = ', '.join(sorted(allowed_model_types))
                        rec = (
                            f"Document type mismatch. Selected '{selected_doc_type}', "
                            f"but trained model detected {detect_class} ({detected_type}). "
                            "Document was not marked valid."
                        )
                        all_issues.append(
                            f"Document type mismatch: selected '{selected_doc_type}' expects {expected}, "
                            f"but model detected {detect_label} ({detected_type}) at {model_confidence}% confidence."
                        )
                    else:
                        rec = (
                            f"Low-confidence model guess: {detect_class}. "
                            f"Description: {detect_label}. "
                            f"Confidence: {model_confidence}%, below required {MIN_VALID_CONFIDENCE}%. "
                            "Document was not marked valid."
                        )
                        all_issues.append(
                            f"Low-confidence trained model guess: {detect_label} ({model_confidence}%)."
                        )
            else:
                final_score = 0
                status = 'Fake'
                rec = 'Document was not recognized by the trained model. Treat as fake or unsupported.'
                error = detect.get('error', '')
                issue = 'No trained model document class detected.'
                if error:
                    issue += f" Detector error: {error}"
                all_issues.append(issue)

        issues_str = '; '.join(all_issues)

        cur.execute(
            "SELECT id FROM verifications WHERE document_id = %s",
            (doc_id,)
        )
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """UPDATE verifications SET
                   authenticity_score=%s, status=%s,
                   issues=%s, recommendation=%s, verified_at=NOW()
                   WHERE document_id=%s""",
                (final_score, status, issues_str, rec, doc_id)
            )
        else:
            cur.execute(
                """INSERT INTO verifications
                   (candidate_id, document_id, authenticity_score,
                    status, issues, recommendation, verified_at)
                   VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                (candidate_id, doc_id, final_score, status, issues_str, rec)
            )

        conn.commit()
        cur.close()
        conn.close()
        print(f"Verification complete: {status} ({final_score}%)")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
