import sys
import json
import re

def extract_names(text):
    words = text.upper().split()
    names = [w for w in words if len(w) > 2 and w.isalpha()]
    return set(names)

def extract_dates(text):
    patterns = [
        r'\d{2}/\d{2}/\d{4}',
        r'\d{2}-\d{2}-\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}\.\d{2}\.\d{4}'
    ]
    dates = []
    for p in patterns:
        dates.extend(re.findall(p, text))
    return set(dates)

def cross_check(texts):
    try:
        if len(texts) < 2:
            return {
                "success": True,
                "consistent": True,
                "issues": [],
                "score": 100
            }

        issues = []
        score = 100

        # Extract names from all documents
        all_names = [extract_names(t) for t in texts]

        # Check name consistency across docs
        common_names = all_names[0]
        for names in all_names[1:]:
            common_names = common_names.intersection(names)

        if len(common_names) == 0:
            issues.append("No matching names found across documents")
            score -= 30

        # Extract and compare dates
        all_dates = [extract_dates(t) for t in texts]
        has_dates = [d for d in all_dates if len(d) > 0]

        if len(has_dates) >= 2:
            common_dates = has_dates[0]
            for dates in has_dates[1:]:
                common_dates = common_dates.intersection(dates)
            if len(common_dates) == 0:
                issues.append("Date of birth does not match across documents")
                score -= 25

        score = max(0, score)

        return {
            "success": True,
            "consistent": len(issues) == 0,
            "issues": issues,
            "score": score,
            "common_names": list(common_names)
        }

    except Exception as e:
        return {"success": False, "error": str(e), "score": 50, "issues": []}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No texts provided", "score": 50, "issues": []}))
    else:
        texts = json.loads(sys.argv[1])
        result = cross_check(texts)
        print(json.dumps(result))