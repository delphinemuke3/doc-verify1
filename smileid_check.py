import sys
import json
import requests
import base64
import hashlib
import time
import hmac
import os

def generate_signature(partner_id, api_key):
    timestamp = str(int(time.time()))
    msg = f"{partner_id}:{timestamp}"
    signature = hmac.new(
        api_key.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature, timestamp

def encode_image(image_path):
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def verify_document(image_path, candidate_name, partner_id, api_key, sandbox=True):
    try:
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": "File not found",
                "smile_score": 50,
                "issues": [],
                "positives": []
            }

        signature, timestamp = generate_signature(partner_id, api_key)
        image_b64 = encode_image(image_path)

        server = "https://testapi.smileidentity.com/v1" if sandbox \
                 else "https://api.smileidentity.com/v1"

        job_id  = f"doc-verify-{int(time.time())}"
        user_id = f"candidate-{hashlib.md5(candidate_name.encode()).hexdigest()[:8]}"

        # Job type 6 = Document Verification
        payload = {
            "source_sdk":         "PHP",
            "source_sdk_version": "1.0.0",
            "partner_id":         partner_id,
            "timestamp":          timestamp,
            "signature":          signature,
            "smile_client_id":    user_id,
            "partner_params": {
                "job_id":   job_id,
                "user_id":  user_id,
                "job_type": 6
            },
            "id_info": {
                "country":  "RW",
                "id_type":  "NATIONAL_ID",
                "entered":  True
            },
            "images": [
                {
                    "image_type_id": 3,
                    "image":         image_b64
                }
            ],
            "options": {
                "return_job_status":      True,
                "return_image_links":     False,
                "return_history":         False,
                "signature":              True
            }
        }

        response = requests.post(
            f"{server}/smile_jobs",
            json=payload,
            timeout=60
        )

        data = response.json()

        if response.status_code != 200:
            return {
                "success":      False,
                "error":        data.get('error', 'API error'),
                "smile_score":  50,
                "issues":       ["Smile ID API returned an error"],
                "positives":    []
            }

        result  = data.get('result', {})
        actions = result.get('Actions', {})
        issues  = []
        positives = []
        smile_score = 50

        # Parse Smile ID result
        result_text = result.get('ResultText', '')
        result_code = result.get('ResultCode', '')

        # Document verification result
        doc_verify = actions.get('Verify_Document', '')
        if doc_verify == 'Passed':
            positives.append("Smile ID: Document verified as authentic")
            smile_score += 30
        elif doc_verify == 'Failed':
            issues.append("Smile ID: Document verification FAILED")
            smile_score -= 30
        elif doc_verify == 'Caution':
            issues.append("Smile ID: Document requires manual review")
            smile_score -= 10

        # Return personal info
        if actions.get('Return_Personal_Info') == 'Returned':
            full_name = result.get('FullName', '')
            dob       = result.get('DOB', '')
            id_number = result.get('IDNumber', '')

            if full_name:
                positives.append(f"Smile ID: Name confirmed — {full_name}")
                smile_score += 10

                # Cross-check name with candidate
                if candidate_name:
                    name_parts  = candidate_name.upper().split()
                    api_name_up = full_name.upper()
                    matches = sum(1 for p in name_parts if p in api_name_up)
                    ratio   = matches / len(name_parts) if name_parts else 0

                    if ratio >= 0.8:
                        positives.append(
                            "Smile ID: Candidate name matches ID record — identity confirmed"
                        )
                        smile_score += 15
                    elif ratio >= 0.5:
                        issues.append(
                            "Smile ID: Partial name match with ID record"
                        )
                    else:
                        issues.append(
                            f"Smile ID: Name mismatch — ID shows '{full_name}' "
                            f"but candidate is '{candidate_name}'"
                        )
                        smile_score -= 30

            if dob:
                positives.append(f"Smile ID: Date of birth confirmed — {dob}")
                smile_score += 5

            if id_number:
                positives.append(f"Smile ID: ID number confirmed — {id_number}")
                smile_score += 5

        # Face/selfie comparison
        selfie_check = actions.get('Selfie_To_ID_Card_Compare', '')
        if selfie_check == 'Completed':
            positives.append("Smile ID: Face matched to ID photo")
            smile_score += 10
        elif selfie_check == 'Failed':
            issues.append("Smile ID: Face did NOT match ID photo")
            smile_score -= 20

        # Liveness
        liveness = actions.get('Liveness_Check', '')
        if liveness == 'Passed':
            positives.append("Smile ID: Liveness check passed")
            smile_score += 5
        elif liveness == 'Failed':
            issues.append("Smile ID: Liveness check failed")
            smile_score -= 15

        smile_score = min(100, max(0, smile_score))

        return {
            "success":      True,
            "smile_score":  smile_score,
            "result_text":  result_text,
            "result_code":  result_code,
            "full_name":    result.get('FullName', ''),
            "dob":          result.get('DOB', ''),
            "id_number":    result.get('IDNumber', ''),
            "job_id":       job_id,
            "issues":       issues,
            "positives":    positives,
            "raw_actions":  actions
        }

    except requests.exceptions.Timeout:
        return {
            "success":     False,
            "error":       "Smile ID API timeout",
            "smile_score": 50,
            "issues":      ["Smile ID API timed out — using local checks only"],
            "positives":   []
        }
    except Exception as e:
        return {
            "success":     False,
            "error":       str(e),
            "smile_score": 50,
            "issues":      [],
            "positives":   []
        }

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(json.dumps({
            "success": False,
            "error": "Usage: smileid_check.py <image> <name> <partner_id> <api_key>"
        }))
    else:
        image_path     = sys.argv[1]
        candidate_name = sys.argv[2]
        partner_id     = sys.argv[3]
        api_key        = sys.argv[4]
        sandbox        = sys.argv[5].lower() == '0' if len(sys.argv) > 5 else True
        print(json.dumps(
            verify_document(image_path, candidate_name, partner_id, api_key, sandbox)
        ))