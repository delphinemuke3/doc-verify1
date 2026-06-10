<?php
session_start();
// DOCVERIFY_VERSION: v3-2026-06-06

// ─── helpers ───────────────────────────────────────────────────────────────

function run_python(string $script, array $args): array {
    $escaped = array_map('escapeshellarg', $args);
    $cmd     = 'python ' . escapeshellarg($script) . ' ' . implode(' ', $escaped) . ' 2>&1';
    $output  = shell_exec($cmd);
    if (!$output || trim($output) === '') {
        return ['error' => 'No output from Python script', 'raw' => ''];
    }
    // Strip any non-JSON prefix (e.g. warnings printed before JSON)
    $json_start = strpos($output, '{');
    if ($json_start === false) {
        return ['error' => 'No JSON in output', 'raw' => $output];
    }
    $decoded = json_decode(substr($output, $json_start), true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return ['error' => 'JSON parse failed: ' . json_last_error_msg(), 'raw' => $output];
    }
    return $decoded;
}

function safe_str(mixed $v): string {
    return is_string($v) ? trim($v) : (is_null($v) ? '' : (string)$v);
}

// Correctly parse Python's True/False/None into PHP true/false/null
function safe_bool(mixed $v): ?bool {
    if ($v === true  || $v === 1)    return true;
    if ($v === false || $v === 0)    return false;
    if ($v === null)                 return null;
    if (is_string($v)) {
        $l = strtolower(trim($v));
        if ($l === 'true'  || $l === '1') return true;
        if ($l === 'false' || $l === '0') return false;
    }
    return null;
}

// ─── paths ─────────────────────────────────────────────────────────────────

$base_dir   = dirname(__DIR__);
$upload_dir = $base_dir . '/uploads/';
$py         = $base_dir . '/python/';

if (!is_dir($upload_dir)) mkdir($upload_dir, 0777, true);

// ─── form input ────────────────────────────────────────────────────────────

$candidate_name = trim($_POST['candidate_name'] ?? '');
$file           = $_FILES['document'] ?? null;

if (!$candidate_name || !$file || $file['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    die('Missing candidate name or file.');
}

$ext      = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
$filename = uniqid('doc_', true) . '.' . $ext;
$filepath = $upload_dir . $filename;

if (!move_uploaded_file($file['tmp_name'], $filepath)) {
    http_response_code(500);
    die('Failed to save uploaded file.');
}

// ─── step 1: AI document detection ─────────────────────────────────────────

$detect = run_python($py . 'detect.py', [$filepath]);

$detect_class      = safe_str($detect['class']       ?? '');
$detect_confidence = (float)($detect['confidence']   ?? 0);
$detect_verified   = ($detect['verified']            ?? false) === true;
$detect_desc       = safe_str($detect['description'] ?? '');
$detect_threshold  = (float)($detect['threshold']    ?? 40);

// ─── step 2: QR verification ───────────────────────────────────────────────
// qr_check.py returns these keys (CONFIRMED from source):
//   success, qr_found, trusted, verified_online, name_match,
//   extracted_name, institution, qr_url, online_status, issues, positives

$qr = run_python($py . 'qr_check.py', [$filepath, $candidate_name]);

// Debug log — remove in production
error_log('QR RAW: ' . json_encode($qr));

// Read using the EXACT key names qr_check.py outputs
$qr_found        = ($qr['qr_found']        ?? false) === true;
$qr_verified     = ($qr['verified_online'] ?? false) === true;  // key = verified_online
$qr_institution  = safe_str($qr['institution']  ?? '');
$qr_url          = safe_str($qr['qr_url']       ?? '');         // key = qr_url
$qr_status       = safe_str($qr['online_status'] ?? '');        // key = online_status
$cert_holder     = safe_str($qr['extracted_name'] ?? '');       // key = extracted_name
$name_match      = safe_bool($qr['name_match']    ?? null);     // key = name_match
$py_issues_raw   = is_array($qr['issues'] ?? null) ? $qr['issues'] : [];

// ─── step 3: scoring & issues ──────────────────────────────────────────────
//
//  name_match === false  →  borrowed certificate  →  50%, SUSPICIOUS
//  name_match === true   →  name confirmed        →  keep base score
//  name_match === null   →  unknown               →  keep base score, no penalty
//
$issues   = [];
$borrowed = false;

// Base score from AI detection
if ($detect_verified) {
    $base_score = 100;
} elseif ($detect_confidence >= $detect_threshold) {
    $base_score = 70;
} else {
    $base_score = 30;
    $issues[]   = '✗ Document type could not be confirmed by AI model.';
}

// Name match penalty
if ($name_match === false) {
    $borrowed = true;
    $score    = 50;
    $holder_display = $cert_holder ?: 'unknown';
    $issues[] = '✗ BORROWED CERTIFICATE — QR confirms this certificate belongs to \''
              . $holder_display . '\', not candidate \'' . $candidate_name . '\'.';
} else {
    $score = $base_score;
}

// Merge other Python issues (deduplicated, skip raw name-mismatch lines)
foreach ($py_issues_raw as $pi) {
    $pi = safe_str($pi);
    if ($pi === '') continue;
    if (stripos($pi, 'NAME MISMATCH') !== false)              continue; // covered above
    if (stripos($pi, 'BORROWED')      !== false)              continue;
    if (stripos($pi, 'does not match candidate') !== false)   continue;
    if (!in_array($pi, $issues, true)) {
        $issues[] = $pi;
    }
}

// ─── step 4: overall status ────────────────────────────────────────────────

if ($borrowed) {
    $status       = 'Suspicious';
    $status_class = 'suspicious';
    $verdict      = 'Document type confirmed by AI but name mismatch via QR. Manual review required.';
} elseif ($score >= 80) {
    $status       = 'Verified';
    $status_class = 'verified';
    $holder_note  = ($cert_holder && $name_match === true)
                  ? ' Name verified: ' . $cert_holder . '.'
                  : '';
    $verdict      = 'Document matches trained model class: ' . $detect_class . '. '
                  . 'Confidence: ' . number_format($detect_confidence, 1) . '% (required ' . (int)$detect_threshold . '%). '
                  . ($qr_verified ? 'QR verified online at ' . ($qr_institution ?: 'institution') . '.' : '')
                  . $holder_note
                  . ' Candidate may proceed.';
} elseif ($score >= 50) {
    $status       = 'Suspicious';
    $status_class = 'suspicious';
    $verdict      = 'Document partially verified. Manual review recommended.';
} else {
    $status       = 'Unverified';
    $status_class = 'unverified';
    $verdict      = 'Document could not be verified. AI confidence too low or critical checks failed.';
}

$verified_at = date('M d, Y H:i');
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verification Result — DocVerify</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>
body { font-family: 'Segoe UI', sans-serif; background: #f4f6f9; margin: 0; }
.container { max-width: 860px; margin: 40px auto; padding: 0 20px 60px; }

/* banners */
.alert { border-radius: 8px; padding: 18px 22px; margin-bottom: 22px; font-size: 15px; line-height: 1.6; }
.alert-danger  { background: #fef2f2; border-left: 5px solid #dc2626; color: #991b1b; }
.alert-warning { background: #fffbeb; border-left: 5px solid #f59e0b; color: #92400e; }
.alert-success { background: #f0fdf4; border-left: 5px solid #16a34a; color: #14532d; }
.alert h3 { margin: 0 0 8px; font-size: 17px; }
.alert p  { margin: 4px 0 0; }

/* cards */
.card { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 24px 28px; margin-bottom: 22px; }
.card h2 { margin: 0 0 18px; font-size: 17px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }
.info-row { display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: #64748b; font-weight: 600; min-width: 160px; }
.info-value { color: #1e293b; text-align: right; flex: 1; }

/* score badge */
.score-badge { display: inline-block; padding: 6px 18px; border-radius: 20px; font-weight: 700; font-size: 18px; }
.score-verified   { background: #dcfce7; color: #15803d; }
.score-suspicious { background: #fef9c3; color: #a16207; }
.score-unverified { background: #fee2e2; color: #b91c1c; }

/* pills */
.pill { border-radius: 12px; padding: 3px 12px; font-size: 13px; font-weight: 600; }
.pill-verified   { background: #dcfce7; color: #15803d; }
.pill-suspicious { background: #fef9c3; color: #a16207; }
.pill-unverified { background: #fee2e2; color: #b91c1c; }

/* issues */
.issues-list { list-style: none; margin: 0; padding: 0; }
.issues-list li { padding: 8px 0; font-size: 14px; border-bottom: 1px solid #f1f5f9; color: #374151; }
.issues-list li:last-child { border-bottom: none; }
.no-issues { color: #16a34a; font-size: 14px; margin: 0; }

.btn { display: inline-block; padding: 11px 28px; border-radius: 7px; text-decoration: none; font-weight: 600; font-size: 14px; margin-right: 8px; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-primary:hover { background: #2563eb; }
.btn-secondary { background: #64748b; color: #fff; }
.btn-secondary:hover { background: #475569; }
</style>
</head>
<body>
<div class="container">

  <h1 style="color:#1e293b;margin-bottom:24px;">Verification Result</h1>

  <?php if ($borrowed): ?>
  <div class="alert alert-danger">
    <h3>✗ BORROWED CERTIFICATE DETECTED</h3>
    <p>QR online verification <strong>confirms</strong> this certificate belongs to a different person.</p>
    <p>
      Candidate: <strong><?= htmlspecialchars($candidate_name) ?></strong>
      &nbsp;|&nbsp;
      Certificate holder: <strong><?= htmlspecialchars($cert_holder ?: 'unknown') ?></strong>
    </p>
    <p><strong>Reject this application immediately and investigate further.</strong></p>
  </div>

  <?php elseif ($score < 50): ?>
  <div class="alert alert-danger">
    <h3>✗ DOCUMENT NOT VERIFIED</h3>
    <p>AI confidence is too low to confirm document type. Manual inspection required.</p>
  </div>

  <?php elseif ($score < 80): ?>
  <div class="alert alert-warning">
    <h3>⚠ SUSPICIOUS — Manual Review Required</h3>
    <p><?= htmlspecialchars($verdict) ?></p>
  </div>

  <?php else: ?>
  <div class="alert alert-success">
    <h3>✓ DOCUMENT VERIFIED</h3>
    <p><?= htmlspecialchars($verdict) ?></p>
  </div>
  <?php endif; ?>

  <!-- QR Card -->
  <div class="card">
    <h2>QR Code Verification</h2>
    <div class="info-row">
      <span class="info-label">Institution</span>
      <span class="info-value"><?= htmlspecialchars($qr_institution ?: '—') ?></span>
    </div>
    <div class="info-row">
      <span class="info-label">URL</span>
      <span class="info-value">
        <?= $qr_url
            ? '<a href="' . htmlspecialchars($qr_url) . '" target="_blank">' . htmlspecialchars($qr_url) . '</a>'
            : '—' ?>
      </span>
    </div>
    <div class="info-row">
      <span class="info-label">Status</span>
      <span class="info-value">
        <?php if ($qr_verified): ?>
          <span style="color:#16a34a;font-weight:600;">✓ Online verified</span>
        <?php else: ?>
          <?= htmlspecialchars($qr_status ?: '—') ?>
        <?php endif; ?>
      </span>
    </div>

    <?php if ($cert_holder): ?>
    <div class="info-row">
      <span class="info-label">Name on Certificate</span>
      <span class="info-value"><strong><?= htmlspecialchars($cert_holder) ?></strong>
        <span style="color:#64748b;font-size:12px;margin-left:6px;">(from QR portal)</span>
      </span>
    </div>
    <?php endif; ?>

    <div class="info-row">
      <span class="info-label">Candidate Name</span>
      <span class="info-value"><?= htmlspecialchars($candidate_name) ?></span>
    </div>

    <div class="info-row">
      <span class="info-label">Name Match</span>
      <span class="info-value">
        <?php if (!$qr_found): ?>
          <span style="color:#64748b;">— No QR code found on document</span>
        <?php elseif (!$qr_verified): ?>
          <span style="color:#64748b;">— Portal not reachable, name not checked</span>
        <?php elseif ($name_match === true): ?>
          <span style="color:#16a34a;font-weight:600;">
            ✓ Match — <em><?= htmlspecialchars($candidate_name) ?></em>
            confirmed on portal
          </span>
        <?php elseif ($name_match === false): ?>
          <span style="color:#dc2626;font-weight:600;">
            ✗ Mismatch — portal shows
            <em><?= htmlspecialchars($cert_holder ?: 'different person') ?></em>,
            not <em><?= htmlspecialchars($candidate_name) ?></em>
          </span>
        <?php else: ?>
          <span style="color:#d97706;">— Portal loaded but name could not be extracted</span>
        <?php endif; ?>
      </span>
    </div>

    <?php if ($qr_verified && $name_match === true): ?>
    <div style="margin-top:12px;padding:10px 14px;background:#f0fdf4;border-radius:6px;border-left:3px solid #16a34a;font-size:13px;color:#15803d;">
      ✓ QR portal at <strong><?= htmlspecialchars($qr_institution) ?></strong> confirms
      this certificate belongs to <strong><?= htmlspecialchars($candidate_name) ?></strong>.
    </div>
    <?php elseif ($qr_verified && $name_match === false): ?>
    <div style="margin-top:12px;padding:10px 14px;background:#fef2f2;border-radius:6px;border-left:3px solid #dc2626;font-size:13px;color:#991b1b;">
      ✗ QR portal confirms this certificate belongs to
      <strong><?= htmlspecialchars($cert_holder ?: 'a different person') ?></strong>,
      not candidate <strong><?= htmlspecialchars($candidate_name) ?></strong>.
      This is a borrowed certificate.
    </div>
    <?php endif; ?>
  </div>

  <!-- Score Card -->
  <div class="card">
    <h2>Authenticity Score</h2>
    <div class="info-row">
      <span class="info-label">Score</span>
      <span class="info-value">
        <span class="score-badge score-<?= $status_class ?>">
          <?= $score ?>% <?= $status ?>
        </span>
      </span>
    </div>
    <p style="margin:14px 0 0;font-size:14px;color:#475569;"><?= htmlspecialchars($verdict) ?></p>
  </div>

  <!-- Document Info Card -->
  <div class="card">
    <h2>Document Info</h2>
    <div class="info-row"><span class="info-label">Candidate</span>     <span class="info-value"><?= htmlspecialchars($candidate_name) ?></span></div>
    <div class="info-row"><span class="info-label">Document type</span> <span class="info-value"><?= htmlspecialchars($detect_class ?: 'Unknown') ?></span></div>
    <div class="info-row"><span class="info-label">Score</span>          <span class="info-value"><?= $score ?>%</span></div>
    <div class="info-row"><span class="info-label">Model class</span>   <span class="info-value"><?= htmlspecialchars($detect_class ?: '—') ?></span></div>
    <div class="info-row"><span class="info-label">Confidence</span>    <span class="info-value"><?= number_format($detect_confidence, 1) ?>% (required <?= (int)$detect_threshold ?>%)</span></div>
    <div class="info-row"><span class="info-label">Description</span>   <span class="info-value"><?= htmlspecialchars($detect_desc ?: '—') ?></span></div>
    <div class="info-row">
      <span class="info-label">Status</span>
      <span class="info-value"><span class="pill pill-<?= $status_class ?>"><?= $status ?></span></span>
    </div>
    <div class="info-row"><span class="info-label">Verified at</span>   <span class="info-value"><?= $verified_at ?></span></div>
  </div>

  <!-- Issues Card -->
  <div class="card">
    <h2>Issues Found</h2>
    <?php if (empty($issues)): ?>
      <p class="no-issues">✓ No issues detected. Document passed all checks.</p>
    <?php else: ?>
      <ul class="issues-list">
        <?php foreach ($issues as $issue): ?>
          <li><?= htmlspecialchars($issue) ?></li>
        <?php endforeach; ?>
      </ul>
    <?php endif; ?>
  </div>

  <a href="verify.php" class="btn btn-primary">Upload Another</a>
  <a href="../index.php" class="btn btn-secondary">Dashboard</a>

  <p style="margin-top:30px;font-size:11px;color:#94a3b8;text-align:center;">
    DocVerify v3 &mdash; <?= date('Y') ?>
  </p>

</div>
</body>
</html>