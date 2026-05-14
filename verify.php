<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$result     = null;
$error      = null;
$uploadedImg = null;
$detectedImg = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['document'])) {
    $file       = $_FILES['document'];
    $allowed    = ['image/jpeg', 'image/png', 'image/jpg'];
    $maxSize    = 10 * 1024 * 1024; // 10MB

    if (!in_array($file['type'], $allowed)) {
        $error = 'Only JPG and PNG images are supported.';
    } elseif ($file['size'] > $maxSize) {
        $error = 'File too large. Maximum size is 10MB.';
    } elseif ($file['error'] !== UPLOAD_ERR_OK) {
        $error = 'Upload failed. Please try again.';
    } else {
        // Save uploaded file
        if (!is_dir(UPLOAD_DIR)) mkdir(UPLOAD_DIR, 0755, true);

        $ext        = pathinfo($file['name'], PATHINFO_EXTENSION);
        $filename   = 'doc_' . time() . '_' . uniqid() . '.' . $ext;
        $filepath   = UPLOAD_DIR . $filename;
        $confidence = isset($_POST['confidence']) ? (int)$_POST['confidence'] : DETECTION_CONFIDENCE;

        if (move_uploaded_file($file['tmp_name'], $filepath)) {
            // Run YOLOv8 detection
            $cmd    = PYTHON_PATH . ' ' . escapeshellarg(PYTHON_DETECT)
                    . ' ' . escapeshellarg($filepath)
                    . ' ' . escapeshellarg($confidence)
                    . ' 2>&1';
            $output = shell_exec($cmd);
            $result = json_decode($output, true);

            if (!$result) {
                $error = 'Detection failed. Make sure Python and Ultralytics are installed.';
                $error .= '<br><small>' . htmlspecialchars($output) . '</small>';
            } else {
                $uploadedImg = 'uploads/' . $filename;

                // Path to annotated output image
                $base = pathinfo($filepath, PATHINFO_FILENAME);
                $detectedFile = $base . '_detected.' . $ext;
                if (file_exists(UPLOAD_DIR . $detectedFile)) {
                    $detectedImg = 'uploads/' . $detectedFile;
                }

                // Save result to DB
                if ($result['success']) {
                    $db          = getDB();
                    $userId      = (int)$_SESSION['user_id'];
                    $verified    = $result['verified'] ? 1 : 0;
                    $score       = (float)$result['score'];
                    $detections  = $db->real_escape_string(json_encode($result['detections']));
                    $imagePath   = $db->real_escape_string($uploadedImg);
                    $candidateName = $db->real_escape_string($_POST['candidate_name'] ?? '');

                    $db->query("INSERT INTO verifications 
                        (user_id, candidate_name, image_path, verified, score, detections, created_at)
                        VALUES ($userId, '$candidateName', '$imagePath', $verified, $score, '$detections', NOW())");
                    $db->close();
                }
            }
        } else {
            $error = 'Could not save uploaded file.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verify Document — Gov Doc Verifier</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#f5f6fa;color:#222;min-height:100vh}
.navbar{background:#fff;border-bottom:1px solid #e5e7eb;padding:0 2rem;display:flex;align-items:center;justify-content:space-between;height:56px}
.navbar .brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:16px;color:#185FA5;text-decoration:none}
.navbar .brand span{font-size:22px}
.navbar nav a{color:#555;text-decoration:none;margin-left:1.5rem;font-size:14px}
.navbar nav a:hover{color:#185FA5}
.container{max-width:1000px;margin:2rem auto;padding:0 1.5rem}
.page-title{font-size:22px;font-weight:600;margin-bottom:0.25rem}
.page-sub{font-size:14px;color:#666;margin-bottom:1.5rem}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:1.5rem}
.card-title{font-size:13px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.05em;margin-bottom:1rem}
.form-group{margin-bottom:1rem}
.form-group label{display:block;font-size:13px;color:#555;margin-bottom:5px;font-weight:500}
.form-group input[type=text]{width:100%;padding:9px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;outline:none}
.form-group input[type=text]:focus{border-color:#185FA5}
.upload-zone{border:2px dashed #d1d5db;border-radius:10px;padding:2.5rem 1rem;text-align:center;cursor:pointer;transition:background .15s;position:relative}
.upload-zone:hover{background:#f0f4ff;border-color:#185FA5}
.upload-zone input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.upload-zone .icon{font-size:36px;margin-bottom:.5rem}
.upload-zone p{font-size:14px;color:#555}
.upload-zone span{font-size:12px;color:#999}
.slider-row{margin:1rem 0}
.slider-row label{font-size:13px;color:#555;display:flex;justify-content:space-between;margin-bottom:6px;font-weight:500}
.slider-row label span{color:#185FA5;font-weight:600}
input[type=range]{width:100%;accent-color:#185FA5}
.btn{width:100%;padding:11px;background:#185FA5;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;margin-top:.75rem;transition:background .15s}
.btn:hover{background:#0C447C}
.alert-error{background:#FEE2E2;border:1px solid #FCA5A5;border-radius:8px;padding:12px 16px;font-size:14px;color:#991B1B;margin-bottom:1rem}
.result-img{width:100%;border-radius:8px;border:1px solid #e5e7eb;display:block}
.no-result{min-height:180px;display:flex;align-items:center;justify-content:center;background:#f9fafb;border-radius:8px;border:1px solid #e5e7eb;color:#bbb;font-size:14px;flex-direction:column;gap:.5rem}
.no-result .icon{font-size:32px}
.detection-item{display:flex;align-items:center;gap:12px;padding:12px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;background:#fafafa}
.det-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0}
.det-info .det-name{font-size:14px;font-weight:600;color:#222}
.det-info .det-desc{font-size:12px;color:#666}
.conf-bar{height:5px;border-radius:3px;background:#e5e7eb;margin-top:5px;overflow:hidden;width:200px}
.conf-fill{height:100%;border-radius:3px}
.status-verified{background:#D1FAE5;border:1px solid #6EE7B7;border-radius:8px;padding:12px 16px;display:flex;align-items:center;gap:8px;color:#065F46;font-weight:600;font-size:14px;margin-top:1rem}
.status-failed{background:#FEE2E2;border:1px solid #FCA5A5;border-radius:8px;padding:12px 16px;display:flex;align-items:center;gap:8px;color:#991B1B;font-weight:600;font-size:14px;margin-top:1rem}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500}
.badge-id{background:#E6F1FB;color:#0C447C}
.badge-ulk{background:#EAF3DE;color:#3B6D11}
.badge-ur{background:#FAEEDA;color:#633806}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>

<div class="navbar">
  <a class="brand" href="dashboard.php"><span>🇷🇼</span> Gov Doc Verifier</a>
  <nav>
    <a href="dashboard.php">Dashboard</a>
    <a href="verify.php">Verify</a>
    <a href="history.php">History</a>
    <a href="logout.php">Logout</a>
  </nav>
</div>

<div class="container">
  <div class="page-title">Document Verification</div>
  <div class="page-sub">Upload a candidate document to verify its authenticity using AI detection</div>

  <?php if ($error): ?>
    <div class="alert-error"><?= $error ?></div>
  <?php endif; ?>

  <div class="grid">

    <!-- LEFT: Upload Form -->
    <div class="card">
      <div class="card-title">Upload Document</div>
      <form method="POST" enctype="multipart/form-data">

        <div class="form-group">
          <label>Candidate Name (optional)</label>
          <input type="text" name="candidate_name"
                 placeholder="e.g. Jean Paul Mugisha"
                 value="<?= htmlspecialchars($_POST['candidate_name'] ?? '') ?>">
        </div>

        <div class="upload-zone">
          <input type="file" name="document" accept=".jpg,.jpeg,.png" required>
          <div class="icon">📄</div>
          <p>Drop document image here or click to browse</p>
          <span>Supports JPG, PNG — Max 10MB</span>
        </div>

        <div class="slider-row">
          <label>Confidence Threshold
            <span id="conf-val">25%</span>
          </label>
          <input type="range" name="confidence" min="10" max="90" value="25" step="5"
                 oninput="document.getElementById('conf-val').innerText=this.value+'%'">
        </div>

        <button type="submit" class="btn">🔍 Verify Document</button>
      </form>

      <div style="margin-top:1.25rem;padding-top:1rem;border-top:1px solid #f0f0f0">
        <div style="font-size:12px;color:#999;margin-bottom:.5rem;font-weight:600">DETECTS</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          <span class="badge badge-id">Rwanda National ID</span>
          <span class="badge badge-ulk">ULK Transcript</span>
          <span class="badge badge-ur">UR Transcript</span>
        </div>
      </div>
    </div>

    <!-- RIGHT: Results -->
    <div class="card">
      <div class="card-title">Detection Result</div>

      <?php if ($result && $result['success']): ?>

        <?php if ($detectedImg): ?>
          <img src="../<?= htmlspecialchars($detectedImg) ?>" class="result-img" alt="Detection result">
        <?php elseif ($uploadedImg): ?>
          <img src="../<?= htmlspecialchars($uploadedImg) ?>" class="result-img" alt="Uploaded document">
        <?php endif; ?>

        <div style="margin-top:1rem">
          <?php if ($result['verified'] && count($result['detections']) > 0): ?>
            <?php foreach ($result['detections'] as $det): ?>
              <?php
                $badgeClass = 'badge-id';
                $dotColor   = '#185FA5';
                $barColor   = '#185FA5';
                if (str_contains($det['class'], 'ULK')) { $badgeClass='badge-ulk'; $dotColor='#3B6D11'; $barColor='#3B6D11'; }
                if (str_contains($det['class'], 'UR'))  { $badgeClass='badge-ur';  $dotColor='#BA7517'; $barColor='#BA7517'; }
              ?>
              <div class="detection-item">
                <div class="det-dot" style="background:<?= $dotColor ?>"></div>
                <div class="det-info" style="flex:1">
                  <div class="det-name"><?= htmlspecialchars($det['class']) ?></div>
                  <div class="det-desc"><?= htmlspecialchars($det['description']) ?></div>
                  <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
                    <div class="conf-bar">
                      <div class="conf-fill" style="width:<?= $det['confidence'] ?>%;background:<?= $barColor ?>"></div>
                    </div>
                    <span style="font-size:12px;color:#555;font-weight:600"><?= $det['confidence'] ?>%</span>
                  </div>
                </div>
              </div>
            <?php endforeach; ?>

            <div class="status-verified">
              ✅ Document Verified — <?= count($result['detections']) ?> class(es) detected
            </div>

          <?php else: ?>
            <div class="status-failed">
              ❌ No known document detected — possible fake or unsupported type
            </div>
          <?php endif; ?>
        </div>

      <?php else: ?>
        <div class="no-result">
          <div class="icon">🔎</div>
          <div>Upload a document to see results</div>
        </div>
      <?php endif; ?>
    </div>

  </div>
</div>

</body>
</html>
