<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$db           = getDB();
$doc_id       = (int)($_GET['doc_id'] ?? 0);
$candidate_id = (int)($_GET['candidate_id'] ?? 0);

$ver = $db->query(
    "SELECT v.*, d.doc_type, d.file_path
     FROM verifications v
     JOIN documents d ON v.document_id = d.id
     WHERE v.document_id = $doc_id"
)->fetch_assoc();

$candidate = $db->query(
    "SELECT * FROM candidates WHERE id = $candidate_id"
)->fetch_assoc();

if (!$ver) {
    header("Location: verify.php?doc_id=$doc_id&candidate_id=$candidate_id");
    exit;
}

$status      = $ver['status'];
$final_score = $ver['authenticity_score'];
$issues_str  = $ver['issues'] ?? '';
$all_issues  = $issues_str ? explode(';', $issues_str) : [];
$all_issues  = array_filter(array_map('trim', $all_issues));
$file_path   = __DIR__ . '/../' . $ver['file_path'];
$is_pdf      = strtolower(pathinfo($file_path, PATHINFO_EXTENSION)) === 'pdf';

function run_detector_for_result($file_path) {
    if (!defined('PYTHON_PATH') || !defined('PYTHON_DETECT')) {
        return ['success' => false, 'error' => 'Python detector is not configured.'];
    }

    $cmd = '"' . PYTHON_PATH . '" "' . PYTHON_DETECT . '" '
         . escapeshellarg($file_path) . ' '
         . escapeshellarg(DETECTION_CONFIDENCE)
         . ' 2>&1';
    $raw = shell_exec($cmd);
    $decoded = json_decode($raw, true);

    if ($decoded === null && json_last_error() !== JSON_ERROR_NONE) {
        return [
            'success' => false,
            'error' => 'Detector output invalid JSON: ' . json_last_error_msg(),
            'raw' => trim($raw ?? '')
        ];
    }

    return $decoded ?: ['success' => false, 'error' => 'Detector returned no result.'];
}

function expected_model_types_for_doc($doc_type) {
    $mapping = [
        'national_id' => ['id'],
        'driving_license' => ['license'],
        'certificate' => ['certificate', 'degree'],
        'transcript' => ['transcript'],
    ];
    return $mapping[$doc_type] ?? null;
}

$detect_result = $is_pdf
    ? ['success' => false, 'verified' => false, 'score' => 0, 'detections' => []]
    : run_detector_for_result($file_path);
$detect_verified = !empty($detect_result['verified']);
$detect_score = (int)($detect_result['score'] ?? 0);
$model_confidence = $detect_result['model_confidence'] ?? 0;
$top_detection = ($detect_result['detections'] ?? [])[0] ?? null;
$allowed_model_types = expected_model_types_for_doc($ver['doc_type']);
$detected_model_type = $top_detection['type'] ?? 'unknown';
$type_matches = $allowed_model_types !== null && in_array($detected_model_type, $allowed_model_types, true);
$model_confident = $detect_verified && $model_confidence >= MIN_MODEL_CONFIDENCE;
$model_accepted = $model_confident && $type_matches;

if (!$is_pdf && !empty($detect_result['success']) && !$model_accepted) {
    $status = 'Fake';
    $final_score = 0;
    if ($detect_verified && $top_detection && $allowed_model_types === null) {
        $low_conf_issue = "Selected document type '{$ver['doc_type']}' cannot be automatically verified against model class "
            . ($top_detection['class'] ?? 'unknown') . '.';
    } elseif ($detect_verified && $top_detection && !$type_matches) {
        $expected = implode(', ', $allowed_model_types);
        $low_conf_issue = 'Document type mismatch: selected '
            . ucfirst(str_replace('_', ' ', $ver['doc_type']))
            . " expects {$expected}, but model detected "
            . ($top_detection['description'] ?? $top_detection['class'] ?? 'unknown')
            . " ({$detected_model_type}) at {$model_confidence}% confidence.";
    } else {
        $low_conf_issue = $detect_verified && $top_detection
            ? 'Low-confidence trained model guess: '
              . ($top_detection['description'] ?? $top_detection['class'] ?? 'unknown')
              . " ({$model_confidence}%)."
            : 'No trained model document class detected.';
    }

    if (!in_array($low_conf_issue, $all_issues, true)) {
        $all_issues[] = $low_conf_issue;
    }

    if ($detect_verified && $top_detection && !$type_matches) {
        $ver['recommendation'] = 'The trained model result does not match the selected document type. Document was not marked valid.';
    } elseif ($detect_verified && $top_detection) {
        $ver['recommendation'] = 'The model made a low-confidence guess below the required threshold. Document was not marked valid.';
    } else {
        $ver['recommendation'] = 'Document was not recognized by the trained model. Treat as fake or unsupported.';
    }

    $issues_for_db = implode('; ', $all_issues);
    $stmt = $db->prepare(
        "UPDATE verifications SET authenticity_score=?, status=?, issues=?, recommendation=? WHERE document_id=?"
    );
    $stmt->bind_param("dsssi", $final_score, $status, $issues_for_db, $ver['recommendation'], $doc_id);
    $stmt->execute();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Result - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <style>
        .score-circle {
            width:150px; height:150px; border-radius:50%;
            display:flex; flex-direction:column;
            align-items:center; justify-content:center;
            margin:0 auto 20px; font-size:38px; font-weight:700;
        }
        .score-verified   {background:#e8f5e9;color:#2e7d32;border:4px solid #2e7d32;}
        .score-suspicious {background:#fff8e1;color:#f57f17;border:4px solid #f57f17;}
        .score-fake       {background:#ffebee;color:#c62828;border:4px solid #c62828;}
        .result-label {font-size:13px;font-weight:600;margin-top:4px;}
        .issue-item {
            padding:8px 14px;background:#fff8e1;
            border-left:4px solid #f57f17;
            border-radius:4px;margin-bottom:6px;
            font-size:13px;color:#7a5c00;
        }
        .issue-critical {
            padding:8px 14px;background:#ffebee;
            border-left:4px solid #c62828;
            border-radius:4px;margin-bottom:6px;
            font-size:13px;color:#b71c1c;font-weight:600;
        }
        .identity-alert {
            background:#ffebee;border:2px solid #c62828;
            border-radius:10px;padding:16px 20px;
            margin-bottom:20px;color:#b71c1c;font-weight:600;
        }
        .identity-ok {
            background:#e8f5e9;border:2px solid #2e7d32;
            border-radius:10px;padding:16px 20px;
            margin-bottom:20px;color:#1b5e20;font-weight:600;
        }
        .model-card {
            background:#e8f5e9;border:1px solid #a5d6a7;
            border-radius:10px;padding:16px 20px;margin-bottom:20px;
        }
        .model-card.model-fail {
            background:#fff8e1;border-color:#ffe082;
        }
        .model-card h4 {color:#2e7d32;margin:0 0 10px;font-size:15px;}
        .model-card.model-fail h4 {color:#f57f17;}
        .model-grid {
            display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
            gap:10px;margin-top:12px;
        }
        .model-field {
            background:#fff;border-radius:8px;padding:10px 12px;font-size:13px;
        }
        .model-field span {display:block;color:#666;font-size:12px;margin-bottom:3px;}
        .model-field strong {color:#222;}
    </style>
</head>
<body>
<div class="main-layout">
    <div class="sidebar">
        <div class="sidebar-logo">Doc<span>Verify</span></div>
        <nav class="sidebar-nav">
            <a href="dashboard.php">Dashboard</a>
            <a href="candidates.php">Candidates</a>
            <a href="upload.php" class="active">Upload Documents</a>
            <a href="verifications.php">Verifications</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <div class="main-content">
        <div class="page-title">Verification Result</div>

        <!-- Identity banner -->
        <?php
        $name_mismatch = stripos($issues_str, 'IDENTITY MISMATCH') !== false
                      || stripos($issues_str, 'NOT found in document') !== false;
        $name_ok = stripos($issues_str, 'identity confirmed') !== false
                || ($status === 'Verified' && !$name_mismatch);
        ?>
        <?php if ($name_mismatch): ?>
        <div class="identity-alert">
            &#10007; IDENTITY MISMATCH — Document may belong to a different person.
        </div>
        <?php elseif ($name_ok): ?>
        <div class="identity-ok">
            &#10003; IDENTITY CONFIRMED —
            <?= htmlspecialchars($candidate['full_name'] ?? '') ?>
            matches the document.
        </div>
        <?php endif; ?>

        <?php if (!$is_pdf): ?>
        <div class="model-card <?= $model_accepted ? '' : 'model-fail' ?>">
            <h4>
                Trained Model Result -
                <?php if ($model_accepted): ?>
                    <span><?= $detect_score ?>% valid</span>
                <?php elseif ($model_confident && !$type_matches): ?>
                    <span>Type mismatch</span>
                <?php elseif ($detect_verified): ?>
                    <span>Low confidence match</span>
                <?php else: ?>
                    <span>Not recognized</span>
                <?php endif; ?>
            </h4>

            <?php if ($detect_verified && $top_detection): ?>
                <div class="model-grid">
                    <div class="model-field">
                        <span>Class</span>
                        <strong><?= htmlspecialchars($top_detection['class'] ?? '-') ?></strong>
                    </div>
                    <div class="model-field">
                        <span>Description</span>
                        <strong><?= htmlspecialchars($top_detection['description'] ?? '-') ?></strong>
                    </div>
                    <div class="model-field">
                        <span>Category</span>
                        <strong><?= htmlspecialchars(ucfirst($top_detection['type'] ?? 'unknown')) ?></strong>
                    </div>
                    <div class="model-field">
                        <span>Model confidence</span>
                        <strong><?= htmlspecialchars($model_confidence) ?>%</strong>
                    </div>
                </div>
                <?php if ($model_confident && !$type_matches): ?>
                    <p style="color:#7a5c00;font-size:13px;margin:10px 0 0">
                        Selected type is <?= htmlspecialchars(ucfirst(str_replace('_', ' ', $ver['doc_type']))) ?>,
                        but the model detected <?= htmlspecialchars($detected_model_type) ?>. This should not be accepted as valid.
                    </p>
                <?php elseif (!$model_confident): ?>
                    <p style="color:#7a5c00;font-size:13px;margin:10px 0 0">
                        This match is below the required <?= MIN_MODEL_CONFIDENCE ?>% confidence, so it should not be accepted as valid.
                    </p>
                <?php endif; ?>
            <?php else: ?>
                <p style="color:#777;font-size:13px;margin:0">
                    The uploaded document was searched against the trained model, but no known class was detected.
                    <?php if (!empty($detect_result['error'])): ?>
                        <?= htmlspecialchars($detect_result['error']) ?>
                    <?php endif; ?>
                </p>
            <?php endif; ?>
        </div>
        <?php endif; ?>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px">

            <!-- Score -->
            <div class="card" style="text-align:center">
                <div class="card-title">Authenticity Score</div>
                <div class="score-circle score-<?= strtolower($status) ?>">
                    <?= round($final_score) ?>%
                    <div class="result-label"><?= $status ?></div>
                </div>
                <p style="color:#555;font-size:14px;margin-bottom:16px">
                    <?= htmlspecialchars($ver['recommendation']) ?>
                </p>
                <div style="display:flex;gap:12px;justify-content:center">
                    <a href="upload.php?candidate_id=<?= $candidate_id ?>"
                       class="btn btn-primary">Upload Another</a>
                    <a href="report.php?candidate_id=<?= $candidate_id ?>"
                       class="btn btn-success">Full Report</a>
                </div>
            </div>

            <!-- Info -->
            <div class="card">
                <div class="card-title">Document Info</div>
                <table style="width:100%;font-size:14px">
                    <tr>
                        <td style="padding:8px 0;color:#666;width:140px">Candidate</td>
                        <td style="padding:8px 0;font-weight:600">
                            <?= htmlspecialchars($candidate['full_name'] ?? '-') ?>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#666">Document type</td>
                        <td style="padding:8px 0;font-weight:600">
                            <?= ucfirst(str_replace('_',' ',$ver['doc_type'])) ?>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#666">Score</td>
                        <td style="padding:8px 0;font-weight:600">
                            <?= round($final_score) ?>%
                        </td>
                    </tr>
                    <?php if ($top_detection): ?>
                    <tr>
                        <td style="padding:8px 0;color:#666">Model class</td>
                        <td style="padding:8px 0;font-weight:600">
                            <?= htmlspecialchars($top_detection['class'] ?? '-') ?>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#666">Description</td>
                        <td style="padding:8px 0;font-weight:600">
                            <?= htmlspecialchars($top_detection['description'] ?? '-') ?>
                        </td>
                    </tr>
                    <?php endif; ?>
                    <tr>
                        <td style="padding:8px 0;color:#666">Status</td>
                        <td style="padding:8px 0">
                            <span class="badge badge-<?= strtolower($status) ?>">
                                <?= $status ?>
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#666">Verified at</td>
                        <td style="padding:8px 0">
                            <?= !empty($ver['verified_at'])
                                ? date('M d, Y H:i', strtotime($ver['verified_at']))
                                : 'Not recorded' ?>
                        </td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Issues -->
        <div class="card">
            <div class="card-title">Issues Found</div>
            <?php if (empty($all_issues)): ?>
                <p style="color:#2e7d32">
                    No issues detected. Document passed all checks.
                </p>
            <?php else: ?>
                <?php foreach ($all_issues as $issue):
                    $critical = stripos($issue,'IDENTITY MISMATCH') !== false
                             || stripos($issue,'mismatch') !== false;
                ?>
                <div class="<?= $critical?'issue-critical':'issue-item' ?>">
                    <?= $critical?'&#10007;':'&#9888;' ?>
                    <?= htmlspecialchars($issue) ?>
                </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </div>

    </div>
</div>
</body>
</html>
