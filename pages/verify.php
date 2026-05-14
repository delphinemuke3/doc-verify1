<?php
set_time_limit(300);
ini_set('max_execution_time', 300);
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$db = getDB();
$doc_id       = (int)($_GET['doc_id'] ?? 0);
$candidate_id = (int)($_GET['candidate_id'] ?? 0);

if (!$doc_id) { header('Location: candidates.php'); exit; }

$doc = $db->query("SELECT * FROM documents WHERE id = $doc_id")->fetch_assoc();
if (!$doc) { header('Location: candidates.php'); exit; }

$candidate      = $candidate_id ? $db->query("SELECT * FROM candidates WHERE id = $candidate_id")->fetch_assoc() : [];
$candidate_name = $candidate['full_name'] ?? '';

$file_path         = __DIR__ . '/../' . $doc['file_path'];
$is_pdf            = strtolower(pathinfo($file_path, PATHINFO_EXTENSION)) === 'pdf';
$doc_type_selected = $doc['doc_type'];

function run_python($script, $arg, $extra = '') {
    $cmd = PYTHON_PATH . ' "' . $script . '" "' . $arg . '"'
         . ($extra !== '' ? ' ' . escapeshellarg($extra) : '')
         . ' 2>&1';
    $raw = shell_exec($cmd);
    $decoded = json_decode($raw, true);
    if ($decoded === null && json_last_error() !== JSON_ERROR_NONE) {
        return [
            'success' => false,
            'error' => 'Python output invalid JSON: ' . json_last_error_msg() . '. Raw output: ' . trim($raw),
        ];
    }
    return $decoded;
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

$py = __DIR__ . '/../python/';

// ── Default result arrays ─────────────────────────────────────────────────────
$ocr_result = [
    "success"=>false,"text"=>"","word_count"=>0,
    "content_score"=>50,"doc_issues"=>[],"doc_positives"=>[],
    "detected_type"=>"unknown","institutions_found"=>[],
    "name_match_adjustment"=>0,"error"=>""
];
$img_result   = ["success"=>false,"score"=>70,"issues"=>[],"positives"=>[]];
$qr_result    = ["success"=>false,"qr_found"=>false,"trusted"=>false,
                 "issues"=>[],"positives"=>[],"qr_data"=>null];
$face_result  = ["success"=>false,"face_found"=>false,"face_count"=>0,
                 "score"=>60,"issues"=>[],"positives"=>[]];
$cross_result = ["success"=>true,"score"=>100,"issues"=>[],"positives"=>[]];
$smile_result = [
    "success"=>false,"smile_score"=>50,
    "issues"=>[],"positives"=>[],
    "full_name"=>"","dob"=>"","id_number"=>""
];
$ml_result = [
    "success"=>false,"ml_score"=>50,
    "prediction"=>"unknown","issues"=>[],"positives"=>[]
];
$adv_result = [
    "success"=>false,"advanced_score"=>60,
    "uv_score"=>60,"laser_score"=>60,
    "hologram_score"=>60,"microtext_score"=>60,
    "issues"=>[],"positives"=>[]
];
// ── YOLOv8 default ───────────────────────────────────────────────────────────
$detect_result = [
    "success"=>false,"verified"=>false,"score"=>0,
    "detections"=>[],"total_found"=>0
];

if (!$is_pdf) {
    // Image integrity
    // Image integrity checks are disabled in model-only mode.

    // ── YOLOv8 Document Detection ─────────────────────────────────────────────
    $detect_result = run_python($py.'detect.py', $file_path) ?? $detect_result;

}

// ── Cross-document consistency check ─────────────────────────────────────────
// ── Scoring ───────────────────────────────────────────────────────────────────
$img_score     = $img_result['score']                 ?? 70;
$content_score = $ocr_result['content_score']         ?? 70;
$cross_score   = $cross_result['score']               ?? 100;
$face_score    = $face_result['score']                ?? 60;
$smile_score   = $smile_result['smile_score']         ?? 50;
$ml_score      = $ml_result['ml_score']               ?? 50;
$adv_score     = $adv_result['advanced_score']        ?? 60;
$name_adj      = $ocr_result['name_match_adjustment'] ?? 0;
$doc_names     = $ocr_result['found_names'] ?? [];

// YOLOv8 scores
$detect_score   = $detect_result['score']    ?? 0;
$raw_detect_verified= $detect_result['verified'] ?? false;
$detect_verified= $raw_detect_verified;
$detect_bonus   = $detect_verified ? 10 : -5;
$model_confidence = $detect_result['model_confidence'] ?? $detect_score;
$yolo_detected_class = '';
$detected_model_type = 'unknown';
if (!empty($detect_result['detections'])) {
    $yolo_detected_class = $detect_result['detections'][0]['description'] ?? $detect_result['detections'][0]['class'] ?? '';
    $model_confidence = $detect_result['model_confidence'] ?? ($detect_result['detections'][0]['confidence'] ?? $detect_score);
    $detected_model_type = $detect_result['detections'][0]['type'] ?? 'unknown';
}
$model_confident = $detect_verified && $model_confidence >= MIN_MODEL_CONFIDENCE;
$allowed_model_types = expected_model_types_for_doc($doc_type_selected);
$type_matches = $allowed_model_types !== null && in_array($detected_model_type, $allowed_model_types, true);
$model_type_issue = '';
if ($raw_detect_verified && $model_confident && !$type_matches) {
    $expected = $allowed_model_types === null ? 'a specific selected document type' : implode(', ', $allowed_model_types);
    $model_type_issue = 'Document type mismatch: selected '
        . ucfirst(str_replace('_', ' ', $doc_type_selected))
        . " expects {$expected}, but model detected {$yolo_detected_class} ({$detected_model_type}) at {$model_confidence}% confidence.";
}
$detect_verified = $model_confident && $type_matches;
$detect_bonus = $detect_verified ? 10 : -5;

$qr_bonus   = 0;
if ($qr_result['qr_found'])
    $qr_bonus = $qr_result['trusted'] ? 10 : -10;
$inst_bonus = !empty($ocr_result['institutions_found']) ? 5 : 0;

if ($is_pdf) {
    $final_score = round($cross_score * 0.5 + 50);

} elseif ($doc_type_selected === 'national_id') {
    if ($smile_result['success']) {
        $final_score = round(
            ($smile_score   * 0.40) +
            ($img_score     * 0.15) +
            ($content_score * 0.10) +
            ($face_score    * 0.10) +
            ($adv_score     * 0.15) +
            ($cross_score   * 0.10) +
            $qr_bonus + $inst_bonus + $detect_bonus
        );
    } else {
        $final_score = round(
            ($img_score     * 0.18) +
            ($content_score * 0.22) +
            ($face_score    * 0.15) +
            ($adv_score     * 0.20) +
            ($cross_score   * 0.15) +
            ($detect_score  * 0.10) +
            $qr_bonus + $inst_bonus + $detect_bonus
        );
    }
} else {
    // Certificates / transcripts — include YOLOv8 detection score
    $final_score = round(
        ($img_score     * 0.15) +
        ($content_score * 0.25) +
        ($adv_score     * 0.20) +
        ($ml_score      * 0.15) +
        ($cross_score   * 0.15) +
        ($detect_score  * 0.10) +
        ($inst_bonus * 2) + $qr_bonus + $detect_bonus
    );
}

// Cap score if name completely mismatched
if ($name_adj <= -50) $final_score = min($final_score, 45);
$final_score = min(100, max(0, $final_score));
if ($is_pdf) {
    $final_score = 0;
} elseif ($detect_verified) {
    $final_score = 100;
} else {
    $final_score = 0;
}

// ── Image tampering override ──────────────────────────────────────────────────
$tamper_keywords = [
    'manipulation', 'copy-paste', 'copypaste', 'clone', 'cloned',
    'jpeg compression', 'compression pattern', 'tampered'
];
$tampering_detected = false;
foreach ($img_result['issues'] as $issue) {
    if (!is_string($issue)) continue;
    $lower = strtolower($issue);
    foreach ($tamper_keywords as $keyword) {
        if (strpos($lower, $keyword) !== false) {
            $tampering_detected = true;
            break 2;
        }
    }
}

// ── Status ────────────────────────────────────────────────────────────────────
if ($tampering_detected) {
    $final_score = min($final_score, 25);
    $status = 'Fake';
} else {
    if ($detect_verified || $final_score >= 75) $status = 'Verified';
    elseif ($final_score >= 50) $status = 'Suspicious';
    else                         $status = 'Fake';
}

// ── Collect all issues and positives ─────────────────────────────────────────
$all_issues = array_merge(
    $img_result['issues']      ?? [],
    $ocr_result['doc_issues']  ?? [],
    $cross_result['issues']    ?? [],
    $qr_result['issues']       ?? [],
    $face_result['issues']     ?? [],
    $smile_result['issues']    ?? [],
    $ml_result['issues']       ?? [],
    $adv_result['issues']      ?? [],
    $model_type_issue ? [$model_type_issue] : [],
    // YOLOv8 issue if no document type detected
    (!$raw_detect_verified && !$is_pdf) ? ['Trained model did not detect a known document class'] : [],
    ($raw_detect_verified && !$detect_verified && !$model_type_issue && !$is_pdf)
        ? ['Trained model confidence is below the required threshold'] : [],
    ($is_pdf) ? ['PDF uploaded - trained model detection supports image files only'] : []
);

if ($detect_verified && !$tampering_detected) {
    $all_issues = [];
}

// Add tampering critical issue
if ($tampering_detected) {
    $critical_issue = '❌ CRITICAL: Severe image tampering detected - document automatically marked as Fake.';
    if (!in_array($critical_issue, $all_issues, true)) {
        $all_issues[] = $critical_issue;
    }
}

$all_positives = array_merge(
    $img_result['positives']      ?? [],
    $ocr_result['doc_positives']  ?? [],
    $qr_result['positives']       ?? [],
    $face_result['positives']     ?? [],
    $smile_result['positives']    ?? [],
    $ml_result['positives']       ?? [],
    $adv_result['positives']      ?? [],
    // YOLOv8 positive if document type confirmed
    ($detect_verified && !empty($yolo_detected_class))
        ? ['Trained model confirmed document type: ' . $yolo_detected_class . ' (' . $model_confidence . '% confidence). Overall validity set to 100%.']
        : []
);

if (!empty($ocr_result['institutions_found'])) {
    $all_positives[] = 'Recognized Rwandan institution: '
        . implode(', ', array_slice($ocr_result['institutions_found'], 0, 2));
}
if ($is_pdf) $all_positives[] = 'PDF document uploaded successfully';

$detected_type = $ocr_result['detected_type'] ?? 'unknown';

if ($status === 'Verified')
    $recommendation = $detect_verified
        ? 'Document matches a trained model class and selected document type. Marked valid at 100%. Candidate may proceed.'
        : 'Document appears authentic and consistent with official Rwandan documents. Candidate may proceed.';
elseif ($status === 'Suspicious')
    $recommendation = 'Document has irregularities. Request the original and conduct manual verification before proceeding.';
else
    $recommendation = $is_pdf
        ? 'Only JPG and PNG images can be checked by the trained model right now.'
        : ($model_type_issue
            ? 'The trained model result does not match the selected document type. Document was not marked valid.'
            : 'Document was not recognized by the trained model. Treat as fake or unsupported.');

$issues_str = implode('; ', $all_issues);

// ── Save to database ──────────────────────────────────────────────────────────
$existing = $db->query(
    "SELECT id FROM verifications WHERE document_id = $doc_id"
)->fetch_assoc();

if ($existing) {
    $stmt = $db->prepare(
        "UPDATE verifications SET authenticity_score=?, status=?, issues=?,
         recommendation=?, verified_at=NOW() WHERE document_id=?"
    );
    $stmt->bind_param("dsssi", $final_score, $status, $issues_str, $recommendation, $doc_id);
} else {
    $stmt = $db->prepare(
        "INSERT INTO verifications
         (candidate_id, document_id, authenticity_score, status, issues, recommendation, verified_at)
         VALUES (?,?,?,?,?,?,NOW())"
    );
    $verification_candidate_id = $candidate_id ?: null;
    $stmt->bind_param(
        "iidsss",
        $verification_candidate_id, $doc_id, $final_score, $status, $issues_str, $recommendation
    );
}
$stmt->execute();
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
        .score-verified   { background:#e8f5e9; color:#2e7d32; border:4px solid #2e7d32; }
        .score-suspicious { background:#fff8e1; color:#f57f17; border:4px solid #f57f17; }
        .score-fake       { background:#ffebee; color:#c62828; border:4px solid #c62828; }
        .result-label { font-size:13px; font-weight:600; margin-top:4px; }
        .check-row {
            display:flex; justify-content:space-between; align-items:center;
            padding:12px 0; border-bottom:1px solid #f0f0f0; font-size:14px;
        }
        .check-row:last-child { border-bottom:none; }
        .progress-bar { height:8px; background:#eee; border-radius:4px; width:160px; overflow:hidden; }
        .progress-fill { height:100%; border-radius:4px; background:#1a237e; }
        .positive-item {
            padding:8px 14px; background:#e8f5e9; border-left:4px solid #2e7d32;
            border-radius:4px; margin-bottom:6px; font-size:13px; color:#1b5e20;
        }
        .issue-item {
            padding:8px 14px; background:#fff8e1; border-left:4px solid #f57f17;
            border-radius:4px; margin-bottom:6px; font-size:13px; color:#7a5c00;
        }
        .issue-critical {
            padding:8px 14px; background:#ffebee; border-left:4px solid #c62828;
            border-radius:4px; margin-bottom:6px; font-size:13px; color:#b71c1c;
            font-weight:600;
        }
        .check-badge {
            display:inline-flex; align-items:center; gap:6px;
            padding:6px 14px; border-radius:20px;
            font-size:13px; font-weight:600; margin:4px;
        }
        .badge-pass { background:#e8f5e9; color:#2e7d32; }
        .badge-fail { background:#ffebee; color:#c62828; }
        .badge-skip { background:#f5f5f5; color:#888; }
        .badge-warn { background:#fff8e1; color:#f57f17; }
        .smile-card {
            background:#e3f2fd; border:1px solid #90caf9;
            border-radius:10px; padding:16px 20px; margin-bottom:20px;
        }
        .smile-card h4 { color:#1a237e; margin:0 0 10px; font-size:15px; }
        .smile-card p  { color:#333; font-size:13px; margin:4px 0; }
        .adv-card {
            background:#f3e5f5; border:1px solid #ce93d8;
            border-radius:10px; padding:16px 20px; margin-bottom:20px;
        }
        .adv-card h4 { color:#6a1b9a; margin:0 0 10px; font-size:15px; }
        .yolo-card {
            background:#e8f5e9; border:1px solid #a5d6a7;
            border-radius:10px; padding:16px 20px; margin-bottom:20px;
        }
        .yolo-card.yolo-fail {
            background:#fff8e1; border:1px solid #ffe082;
        }
        .yolo-card h4 { color:#2e7d32; margin:0 0 10px; font-size:15px; }
        .yolo-card.yolo-fail h4 { color:#f57f17; }
        .yolo-card p  { color:#333; font-size:13px; margin:4px 0; }
        .identity-alert {
            background:#ffebee; border:2px solid #c62828; border-radius:10px;
            padding:16px 20px; margin-bottom:20px; color:#b71c1c; font-weight:600;
        }
        .identity-ok {
            background:#e8f5e9; border:2px solid #2e7d32; border-radius:10px;
            padding:16px 20px; margin-bottom:20px; color:#1b5e20; font-weight:600;
        }
        .adv-grid {
            display:grid; grid-template-columns:1fr 1fr;
            gap:10px; margin-top:10px;
        }
        .adv-item {
            background:#fff; border-radius:8px;
            padding:10px 14px; font-size:13px;
        }
        .adv-item-label { color:#555; margin-bottom:4px; font-weight:600; }
        .adv-bar { height:6px; background:#eee; border-radius:3px; overflow:hidden; }
        .adv-bar-fill { height:100%; border-radius:3px; }
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

        <!-- Model-only verification -->
        <?php if (false): ?>
        <div class="identity-alert">
            Model-only verification is active.
            <br>Document name matching could not be completed for this file.
        </div>
        <?php endif; ?>

        <!-- Identity alert banner -->
        <?php if ($name_adj < 0): ?>
        <div class="identity-alert">
            &#10007; NAME MISMATCH — The document name does not match the selected candidate.
            <br><strong>Candidate:</strong> "<?= htmlspecialchars($candidate_name) ?>"
            <?php if (!empty($doc_names)): ?>
                <br><strong>Detected document name(s):</strong>
                <?= htmlspecialchars(implode(', ', $doc_names)) ?>
            <?php else: ?>
                <br><strong>Detected:</strong> name could not be confidently located on the document.
            <?php endif; ?>
            <br>This document may belong to someone else and requires manual review.
        </div>
        <?php elseif ($name_adj >= 10): ?>
        <div class="identity-ok">
            &#10003; IDENTITY CONFIRMED —
            "<?= htmlspecialchars($candidate_name) ?>"
            matches the name on this document.
        </div>
        <?php endif; ?>

        <!-- YOLOv8 Detection Card -->
        <?php if (!$is_pdf): ?>
        <div class="yolo-card <?= $detect_verified ? '' : 'yolo-fail' ?>">
            <h4>&#127919; YOLOv8 AI Document Detection —
                <?php if ($detect_verified): ?>
                    <span style="color:#2e7d32"><?= $detect_score ?>% Confirmed</span>
                <?php elseif ($raw_detect_verified && $model_type_issue): ?>
                    <span style="color:#f57f17">Type Mismatch</span>
                <?php elseif ($raw_detect_verified): ?>
                    <span style="color:#f57f17">Low Confidence</span>
                <?php else: ?>
                    <span style="color:#f57f17">Not Detected</span>
                <?php endif; ?>
            </h4>
            <?php if ($raw_detect_verified && !empty($detect_result['detections'])): ?>
                <?php foreach ($detect_result['detections'] as $det): ?>
                    <p>
                        <strong>Document Type:</strong>
                        <?= htmlspecialchars($det['description'] ?? $det['class']) ?>
                        &nbsp;|&nbsp;
                        <strong>Confidence:</strong> <?= $det['confidence'] ?>%
                        &nbsp;|&nbsp;
                        <strong>Category:</strong> <?= ucfirst(htmlspecialchars($det['type'])) ?>
                    </p>
                <?php endforeach; ?>
                <?php if ($detect_verified): ?>
                    <p style="color:#2e7d32;font-size:12px;margin-top:6px">
                        &#10003; Document type has been confirmed by trained AI model
                        <?= $detect_bonus > 0 ? '(+' . $detect_bonus . ' bonus pts applied)' : '' ?>
                    </p>
                <?php else: ?>
                    <p style="color:#7a5c00;font-size:12px;margin-top:6px">
                        <?= htmlspecialchars($model_type_issue ?: 'Model confidence is below the required threshold.') ?>
                    </p>
                <?php endif; ?>
            <?php else: ?>
                <p style="color:#888">
                    The AI model could not identify a known document type in this image.
                    <?= !$is_pdf ? '(-5 pts applied)' : '' ?>
                </p>
            <?php endif; ?>
        </div>
        <?php endif; ?>

        <!-- Smile ID result card -->
        <?php if ($doc_type_selected === 'national_id'): ?>
        <div class="smile-card">
            <h4>Smile ID Verification
                <?php if ($smile_result['success']): ?>
                    — <span style="color:<?= $smile_score>=75?'#2e7d32':($smile_score>=50?'#f57f17':'#c62828') ?>">
                        <?= $smile_score ?>%
                        <?= $smile_score>=75?'Verified':($smile_score>=50?'Suspicious':'Failed') ?>
                    </span>
                <?php else: ?>
                    — <span style="color:#888">Unavailable (using local checks)</span>
                <?php endif; ?>
            </h4>
            <?php if ($smile_result['success']): ?>
                <?php if (!empty($smile_result['full_name'])): ?>
                    <p><strong>Name on ID:</strong> <?= htmlspecialchars($smile_result['full_name']) ?></p>
                <?php endif; ?>
                <?php if (!empty($smile_result['dob'])): ?>
                    <p><strong>Date of birth:</strong> <?= htmlspecialchars($smile_result['dob']) ?></p>
                <?php endif; ?>
                <?php if (!empty($smile_result['id_number'])): ?>
                    <p><strong>ID number:</strong> <?= htmlspecialchars($smile_result['id_number']) ?></p>
                <?php endif; ?>
                <?php if (!empty($smile_result['result_text'])): ?>
                    <p><strong>Result:</strong> <?= htmlspecialchars($smile_result['result_text']) ?></p>
                <?php endif; ?>
            <?php else: ?>
                <p style="color:#888">
                    Smile ID could not be reached.
                    Local AI checks are being used instead.
                </p>
            <?php endif; ?>
        </div>
        <?php endif; ?>

        <!-- Advanced security features card -->
        <?php if ($adv_result['success']): ?>
        <div class="adv-card">
            <h4>Advanced Security Features — Overall: <?= $adv_score ?>%</h4>
            <div class="adv-grid">
                <?php
                $adv_features = [
                    'UV Fluorescent Ink'    => $adv_result['uv_score'],
                    'Laser Engraving'       => $adv_result['laser_score'],
                    'Hologram Detection'    => $adv_result['hologram_score'],
                    'Microtext / Guilloche' => $adv_result['microtext_score'],
                ];
                foreach ($adv_features as $label => $score):
                    $color = $score >= 75 ? '#2e7d32' : ($score >= 50 ? '#f57f17' : '#c62828');
                ?>
                <div class="adv-item">
                    <div class="adv-item-label"><?= $label ?></div>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="adv-bar" style="flex:1">
                            <div class="adv-bar-fill"
                                 style="width:<?= $score ?>%;background:<?= $color ?>"></div>
                        </div>
                        <span style="font-size:13px;font-weight:600;color:<?= $color ?>">
                            <?= $score ?>%
                        </span>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <!-- Quick check badges -->
        <div style="margin-bottom:20px;display:flex;flex-wrap:wrap;gap:4px">

            <?php if (!$is_pdf): ?>
            <span class="check-badge <?= $detect_verified?'badge-pass':'badge-warn' ?>">
                <?= $detect_verified?'&#10003;':'&#9888;' ?>
                Trained Model
                <?= $detect_verified ? '(100% valid)' : '(undetected)' ?>
            </span>
            <?php endif; ?>

            <?php if ($qr_result['qr_found']): ?>
                <span class="check-badge <?= $qr_result['trusted']?'badge-pass':'badge-warn' ?>">
                    <?= $qr_result['trusted']?'&#10003;':'&#9888;' ?>
                    QR Code <?= $qr_result['trusted']?'(trusted)':'(unverified)' ?>
                </span>
            <?php else: ?>
                <span class="check-badge badge-skip">&#8212; No QR Code</span>
            <?php endif; ?>

            <?php if ($doc_type_selected === 'national_id'): ?>
                <span class="check-badge <?= $face_result['face_found']?'badge-pass':'badge-fail' ?>">
                    <?= $face_result['face_found']?'&#10003;':'&#10007;' ?>
                    Face Photo
                    <?= $face_result['face_count']>0?'('.$face_result['face_count'].' found)':'' ?>
                </span>
            <?php endif; ?>

            <span class="check-badge <?= $cross_score>=80?'badge-pass':($cross_score>=50?'badge-warn':'badge-fail') ?>">
                <?= $cross_score>=80?'&#10003;':($cross_score>=50?'&#9888;':'&#10007;') ?>
                Cross-Document
            </span>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px">

            <!-- Score card -->
            <div class="card" style="text-align:center">
                <div class="card-title">Authenticity Score</div>
                <div class="score-circle score-<?= strtolower($status) ?>">
                    <?= $final_score ?>%
                    <div class="result-label"><?= $status ?></div>
                </div>

                <!-- YOLOv8 detected document label -->
                <?php if ($detect_verified && !empty($yolo_detected_class)): ?>
                <div style="margin-bottom:10px">
                    <span style="background:#e8f5e9;color:#2e7d32;padding:4px 14px;
                        border-radius:20px;font-size:12px;font-weight:600">
                        &#127919; AI: <?= htmlspecialchars($yolo_detected_class) ?>
                    </span>
                </div>
                <?php endif; ?>

                <?php if ($detected_type !== 'unknown'): ?>
                <div style="margin-bottom:10px">
                    <span style="background:#e3f2fd;color:#1a237e;padding:4px 14px;
                        border-radius:20px;font-size:12px;font-weight:600">
                        Detected: <?= ucfirst(str_replace('_',' ',$detected_type)) ?>
                    </span>
                </div>
                <?php endif; ?>

                <?php if (false): ?>
                <div style="margin-bottom:10px">
                    <span style="background:#e8f5e9;color:#2e7d32;padding:4px 14px;
                        border-radius:20px;font-size:12px;font-weight:600">
                        <?= htmlspecialchars(
                            implode(', ', array_slice($ocr_result['institutions_found'],0,1))
                        ) ?>
                    </span>
                </div>
                <?php endif; ?>

                <p style="color:#555;font-size:14px;margin-bottom:16px">
                    <?= htmlspecialchars($recommendation) ?>
                </p>
                <div style="display:flex;gap:12px;justify-content:center">
                    <a href="upload.php?candidate_id=<?= $candidate_id ?>"
                       class="btn btn-primary">Upload Another</a>
                    <a href="report.php?candidate_id=<?= $candidate_id ?>"
                       class="btn btn-success">Full Report</a>
                </div>
            </div>

            <!-- Score breakdown -->
            <div class="card">
                <div class="card-title">Score Breakdown</div>

                <?php if (!$is_pdf): ?>
                <div class="check-row">
                    <span>Trained Model Detection <small style="color:#999">(authoritative)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill"
                                 style="width:<?= $detect_score ?>%;background:#2e7d32"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px;
                            color:<?= $detect_verified?'#2e7d32':'#f57f17' ?>">
                            <?= $detect_score ?>%
                            <?php if ($detect_verified): ?>
                                <small style="color:#777">(<?= $model_confidence ?>% confidence)</small>
                            <?php endif; ?>
                        </span>
                    </div>
                </div>
                <?php endif; ?>

                <?php if (false): ?>
                <?php if ($doc_type_selected === 'national_id' && $smile_result['success']): ?>
                <div class="check-row">
                    <span>Smile ID <small style="color:#999">(40%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:<?= $smile_score ?>%"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $smile_score ?>%</span>
                    </div>
                </div>
                <?php endif; ?>

                <div class="check-row">
                    <span>Image Integrity <small style="color:#999">(15–18%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:<?= $img_score ?>%"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $img_score ?>%</span>
                    </div>
                </div>

                <div class="check-row">
                    <span>Content Validation <small style="color:#999">(22–25%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:<?= $content_score ?>%"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $content_score ?>%</span>
                    </div>
                </div>

                <div class="check-row">
                    <span>Advanced Security <small style="color:#999">(20–25%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill"
                                 style="width:<?= $adv_score ?>%;background:#6a1b9a"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $adv_score ?>%</span>
                    </div>
                </div>

                <div class="check-row">
                    <span>ML Classifier <small style="color:#999">(15%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill"
                                 style="width:<?= $ml_score ?>%;background:#0d47a1"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $ml_score ?>%</span>
                    </div>
                </div>

                <?php if ($doc_type_selected === 'national_id'): ?>
                <div class="check-row">
                    <span>Face Detection <small style="color:#999">(15%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:<?= $face_score ?>%"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $face_score ?>%</span>
                    </div>
                </div>
                <?php endif; ?>

                <div class="check-row">
                    <span>Cross-Document <small style="color:#999">(15%)</small></span>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:<?= $cross_score ?>%"></div>
                        </div>
                        <span style="font-weight:600;min-width:36px"><?= $cross_score ?>%</span>
                    </div>
                </div>

                <?php if ($qr_result['qr_found']): ?>
                <div class="check-row">
                    <span>QR Code <small style="color:#999">(bonus/penalty)</small></span>
                    <span style="font-weight:600;
                        color:<?= $qr_result['trusted']?'#2e7d32':'#f57f17' ?>">
                        <?= $qr_result['trusted']?'+10 bonus':'-10 penalty' ?>
                    </span>
                </div>
                <?php endif; ?>

                <?php if (false): ?>
                <div class="check-row">
                    <span>Institution match <small style="color:#999">(bonus)</small></span>
                    <span style="font-weight:600;color:#2e7d32">+5 bonus</span>
                </div>
                <?php endif; ?>
                <?php endif; ?>

                <!-- YOLOv8 bonus/penalty row -->
                <?php if (!$is_pdf): ?>
                <div class="check-row">
                    <span>Trained Model Confirmation <small style="color:#999"><?= $detect_verified?'sets score to 100%':'penalty' ?></small></span>
                    <span style="font-weight:600;color:<?= $detect_bonus>0?'#2e7d32':'#f57f17' ?>">
                        <?= $detect_verified ? '100% valid' : $detect_bonus . ' penalty' ?>
                    </span>
                </div>
                <?php endif; ?>

                <?php if ($qr_result['qr_found'] && !empty($qr_result['qr_data'])): ?>
                <div style="margin-top:10px;padding:10px;background:#f9f9f9;
                            border-radius:6px;font-size:12px">
                    <strong>QR Data:</strong><br>
                    <span style="color:#555;word-break:break-all">
                        <?= htmlspecialchars(substr($qr_result['qr_data'],0,120)) ?>
                    </span>
                </div>
                <?php endif; ?>
            </div>
        </div>

        <!-- What passed -->
        <?php if (!empty($all_positives)): ?>
        <div class="card">
            <div class="card-title">What passed</div>
            <?php foreach ($all_positives as $p): ?>
                <div class="positive-item">&#10003; <?= htmlspecialchars($p) ?></div>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <!-- Issues found -->
        <div class="card">
            <div class="card-title">Issues Found</div>
            <?php if (empty($all_issues)): ?>
                <p style="color:#2e7d32">
                    No issues detected. Document passed all checks.
                </p>
            <?php else: ?>
                <?php foreach ($all_issues as $issue): ?>
                    <?php $is_critical =
                        stripos($issue, 'IDENTITY MISMATCH') !== false ||
                        stripos($issue, 'NOT found') !== false ||
                        stripos($issue, 'mismatch') !== false ||
                        stripos($issue, 'CRITICAL') !== false; ?>
                    <div class="<?= $is_critical?'issue-critical':'issue-item' ?>">
                        <?= $is_critical?'&#10007;':'&#9888;' ?>
                        <?= htmlspecialchars($issue) ?>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </div>

        <!-- Extracted text -->
        <?php if (false): ?>
        <div class="card">
            <div class="card-title">Extracted Text</div>
            <pre style="background:#f9f9f9;padding:16px;border-radius:8px;
                        font-size:13px;overflow-x:auto;white-space:pre-wrap;
                        max-height:250px;overflow-y:auto"><?= htmlspecialchars($ocr_result['text']) ?></pre>
        </div>
        <?php endif; ?>

    </div>
</div>
</body>
</html>
