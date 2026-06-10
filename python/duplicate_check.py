import sys
import os
import json
import hashlib

# ─────────────────────────────────────────────────────────────────────────────
#  duplicate_check.py  —  Detect duplicate/borrowed document submissions
#
#  How it works:
#    1. Compute MD5 + SHA256 hash of the uploaded file
#    2. Query the database for any other document with the same hash
#    3. If found → same file submitted by a different candidate = borrowed cert
#    4. If same candidate re-uploaded same file → warn but don't penalize
#
#  Usage:
#    python duplicate_check.py <file_path> <doc_id> <candidate_id>
#
#  Returns JSON with:
#    checked, duplicate_found, same_candidate, other_candidate,
#    other_doc_id, score_adjustment, issues, positives
# ─────────────────────────────────────────────────────────────────────────────


def compute_file_hash(file_path):
    """Compute MD5 and SHA256 hash of a file."""
    md5    = hashlib.md5()
    sha256 = hashlib.sha256()

    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()
    except Exception as e:
        return None, None


def check_duplicate(file_path, doc_id, candidate_id):
    """
    Check if this file has been submitted before by another candidate.
    Returns dict with duplicate detection results.
    """
    issues    = []
    positives = []

    if not os.path.exists(file_path):
        return {
            "checked":          False,
            "duplicate_found":  False,
            "same_candidate":   False,
            "other_candidate":  None,
            "other_doc_id":     None,
            "score_adjustment": 0,
            "issues":           ["Duplicate check: File not found"],
            "positives":        []
        }

    # ── Step 1: Compute file hash ─────────────────────────────────────────────
    md5_hash, sha256_hash = compute_file_hash(file_path)

    if not md5_hash:
        return {
            "checked":          False,
            "duplicate_found":  False,
            "same_candidate":   False,
            "other_candidate":  None,
            "other_doc_id":     None,
            "score_adjustment": 0,
            "issues":           ["Duplicate check: Could not compute file hash"],
            "positives":        []
        }

    # ── Step 2: Query database for matching hash ──────────────────────────────
    db_module = None
    db_driver = None
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
        return {
            "checked":          False,
            "duplicate_found":  False,
            "same_candidate":   False,
            "other_candidate":  None,
            "other_doc_id":     None,
            "score_adjustment": 0,
            "issues":           ["Duplicate check: No database driver available"],
            "positives":        []
        }

    try:
        config = {
            'host':   'localhost',
            'user':   'root',
            'passwd': '',
            'db':     'doc_verify_db'
        }
        if db_driver == 'mysql.connector':
            config['password'] = config.pop('passwd')
            config['database'] = config.pop('db')

        conn = db_module.connect(**config)
        cur  = conn.cursor()

        # ── Step 3: Store hash for this document ──────────────────────────────
        # Check if file_hash column exists, add if not
        try:
            cur.execute("SELECT file_hash FROM documents WHERE id = %s", (doc_id,))
        except Exception:
            # Column doesn't exist — add it
            try:
                cur.execute(
                    "ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64) NULL"
                )
                conn.commit()
            except Exception:
                pass

        # Update hash for current document
        try:
            cur.execute(
                "UPDATE documents SET file_hash = %s WHERE id = %s",
                (md5_hash, doc_id)
            )
            conn.commit()
        except Exception:
            pass

        # ── Step 4: Search for duplicates ─────────────────────────────────────
        try:
            cur.execute(
                """SELECT d.id, d.candidate_id, c.full_name, d.doc_type
                   FROM documents d
                   LEFT JOIN candidates c ON d.candidate_id = c.id
                   WHERE d.file_hash = %s
                   AND d.id != %s""",
                (md5_hash, doc_id)
            )
            matches = cur.fetchall()
        except Exception:
            matches = []

        cur.close()
        conn.close()

        if not matches:
            positives.append(
                "No duplicate submissions found — this document is unique in the system"
            )
            return {
                "checked":          True,
                "duplicate_found":  False,
                "same_candidate":   False,
                "other_candidate":  None,
                "other_doc_id":     None,
                "file_hash":        md5_hash,
                "score_adjustment": 0,
                "issues":           [],
                "positives":        positives
            }

        # ── Duplicate found ───────────────────────────────────────────────────
        other_doc_id      = matches[0][0]
        other_candidate_id= matches[0][1]
        other_name        = matches[0][2] or "Unknown"
        other_doc_type    = matches[0][3] or "document"

        same_candidate = str(other_candidate_id) == str(candidate_id)

        if same_candidate:
            # Same candidate re-uploaded — warn but don't penalize
            positives.append(
                f"Note: This candidate previously submitted an identical file "
                f"(doc ID: {other_doc_id}) — possible re-upload"
            )
            return {
                "checked":          True,
                "duplicate_found":  True,
                "same_candidate":   True,
                "other_candidate":  other_name,
                "other_doc_id":     other_doc_id,
                "file_hash":        md5_hash,
                "score_adjustment": 0,
                "issues":           [],
                "positives":        positives
            }
        else:
            # Different candidate submitted same file — BORROWED CERTIFICATE
            issues.append(
                f"⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — "
                f"This exact file was previously submitted by '{other_name}' "
                f"(doc ID: {other_doc_id}). "
                f"This is a strong indicator of a borrowed or shared certificate!"
            )
            return {
                "checked":          True,
                "duplicate_found":  True,
                "same_candidate":   False,
                "other_candidate":  other_name,
                "other_doc_id":     other_doc_id,
                "file_hash":        md5_hash,
                "score_adjustment": -60,
                "issues":           issues,
                "positives":        []
            }

    except Exception as e:
        return {
            "checked":          False,
            "duplicate_found":  False,
            "same_candidate":   False,
            "other_candidate":  None,
            "other_doc_id":     None,
            "score_adjustment": 0,
            "issues":           [f"Duplicate check error: {str(e)}"],
            "positives":        []
        }


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({
            "checked": False,
            "error": "Usage: duplicate_check.py <file_path> <doc_id> <candidate_id>"
        }))
        sys.exit(1)

    file_path    = sys.argv[1]
    doc_id       = sys.argv[2]
    candidate_id = sys.argv[3]

    result = check_duplicate(file_path, doc_id, candidate_id)
    print(json.dumps(result, indent=2))