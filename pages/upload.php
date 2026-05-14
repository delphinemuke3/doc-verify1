<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$db = getDB();
$success = '';
$error = '';
$candidate_id = isset($_GET['candidate_id']) ? (int)$_GET['candidate_id'] : 0;

function allowOptionalCandidate($db) {
    $dbName = $db->real_escape_string(DB_NAME);
    foreach (['documents', 'verifications'] as $table) {
        $tableEsc = $db->real_escape_string($table);
        $fkRows = $db->query(
            "SELECT CONSTRAINT_NAME
             FROM information_schema.KEY_COLUMN_USAGE
             WHERE TABLE_SCHEMA = '$dbName'
               AND TABLE_NAME = '$tableEsc'
               AND COLUMN_NAME = 'candidate_id'
               AND REFERENCED_TABLE_NAME = 'candidates'"
        );
        if ($fkRows) {
            while ($fk = $fkRows->fetch_assoc()) {
                $name = $db->real_escape_string($fk['CONSTRAINT_NAME']);
                @$db->query("ALTER TABLE `$tableEsc` DROP FOREIGN KEY `$name`");
            }
        }
        @$db->query("ALTER TABLE `$tableEsc` MODIFY candidate_id INT NULL");
        @$db->query(
            "ALTER TABLE `$tableEsc`
             ADD CONSTRAINT `{$tableEsc}_candidate_optional_fk`
             FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL"
        );
    }
}

// Get all candidates for dropdown
$candidates = $db->query("SELECT id, full_name FROM candidates ORDER BY full_name");

// Handle file upload
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $candidate_id = !empty($_POST['candidate_id']) ? (int)$_POST['candidate_id'] : 0;
    $doc_type = $_POST['doc_type'];
    $confidence = isset($_POST['confidence']) ? (int)$_POST['confidence'] : DETECTION_CONFIDENCE;

    if (empty($_FILES['document']['name'])) {
        $error = 'Please select a file to upload.';
    } else {
        $file = $_FILES['document'];
        $allowed = ['jpg', 'jpeg', 'png', 'pdf'];
        $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));

        if (!in_array($ext, $allowed)) {
            $error = 'Only JPG, PNG, and PDF files are allowed.';
        } elseif ($file['size'] > 5 * 1024 * 1024) {
            $error = 'File size must be under 5MB.';
        } else {
            $filename = uniqid('doc_') . '.' . $ext;
            $filepath = UPLOAD_DIR . $filename;

            if (move_uploaded_file($file['tmp_name'], $filepath)) {
                allowOptionalCandidate($db);
                $rel_path = 'uploads/' . $filename;
                $candidate_param = $candidate_id ?: null;
                $stmt = $db->prepare("INSERT INTO documents (candidate_id, doc_type, file_path) VALUES (?, ?, ?)");
                $stmt->bind_param("iss", $candidate_param, $doc_type, $rel_path);
                if ($stmt->execute()) {
                    $doc_id = $stmt->insert_id;
                    $candidate_name = '';
                    if ($candidate_id) {
                        $cand = $db->query("SELECT full_name FROM candidates WHERE id = $candidate_id")->fetch_assoc();
                        $candidate_name = $cand['full_name'] ?? '';
                    }

                    // Run verification in background
                    $cmd = PYTHON_PATH . ' "' . __DIR__ . '/../python/run_verify.py" '
                         . '"' . $doc_id . '" "' . $candidate_id . '" '
                         . escapeshellarg($candidate_name ?? '') . ' '
                         . escapeshellarg($confidence / 100.0);

                    if (PHP_OS_FAMILY === 'Windows') {
                        pclose(popen('start /B "" ' . $cmd, 'r'));
                    } else {
                        shell_exec($cmd . ' > /dev/null 2>&1 &');
                    }

                    header("Location: verifying.php?doc_id=$doc_id&candidate_id=$candidate_id");
                    exit;
                } else {
                    $error = 'Failed to save document record.';
                }
            } else {
                $error = 'Failed to upload file. Check uploads folder permissions.';
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Documents - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
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
        <div class="page-title">Upload Candidate Documents</div>

        <?php if ($error): ?>
            <div class="alert alert-danger"><?= $error ?></div>
        <?php endif; ?>

        <div class="card">
            <div class="card-title">Select Candidate & Document</div>
            <form method="POST" enctype="multipart/form-data">

                <div class="form-group">
                    <label>Select Candidate</label>
                    <select name="candidate_id">
                        <option value="">-- No candidate --</option>
                        <?php while($c = $candidates->fetch_assoc()): ?>
                            <option value="<?= $c['id'] ?>" 
                                <?= $c['id'] == $candidate_id ? 'selected' : '' ?>>
                                <?= htmlspecialchars($c['full_name']) ?>
                            </option>
                        <?php endwhile; ?>
                    </select>
                </div>

                <div class="form-group">
                    <label>Document Type *</label>
                    <select name="doc_type" required>
                        <option value="">-- Select type --</option>
                        <option value="national_id">National ID Card</option>
                        <option value="driving_license">Driving License</option>
                        <option value="certificate">Academic Certificate</option>
                        <option value="transcript">Academic Transcript</option>
                        <option value="other">Other Document</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Upload File * (JPG, PNG or PDF, max 5MB)</label>
                    <input type="file" name="document" accept=".jpg,.jpeg,.png,.pdf" required>
                </div>

                <div class="form-group">
                    <label>Detection Confidence (0-100, default <?= DETECTION_CONFIDENCE ?>)</label>
                    <input type="number" name="confidence" min="0" max="100" value="<?= DETECTION_CONFIDENCE ?>"
                           placeholder="<?= DETECTION_CONFIDENCE ?>" title="Higher values reduce false positives but may miss detections">
                </div>

                <button type="submit" class="btn btn-primary">Upload & Verify</button>
                <a href="candidates.php" class="btn" 
                   style="background:#eee;color:#333;margin-left:8px">Cancel</a>
            </form>
        </div>

        <!-- Uploaded docs for this candidate -->
        <?php if ($candidate_id): 
            $docs = $db->query("SELECT d.*, v.status, v.authenticity_score 
                FROM documents d 
                LEFT JOIN verifications v ON d.id = v.document_id 
                WHERE d.candidate_id = $candidate_id 
                ORDER BY d.uploaded_at DESC");
        ?>
        <div class="card">
            <div class="card-title">Previously Uploaded Documents</div>
            <?php if ($docs->num_rows > 0): ?>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>File</th>
                        <th>Uploaded</th>
                        <th>Status</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                <?php while($doc = $docs->fetch_assoc()): ?>
                    <tr>
                        <td><?= ucfirst(str_replace('_', ' ', $doc['doc_type'])) ?></td>
                        <td><?= basename($doc['file_path']) ?></td>
                        <td><?= date('M d, Y', strtotime($doc['uploaded_at'])) ?></td>
                        <td>
                            <?php if($doc['status']): ?>
                                <span class="badge badge-<?= strtolower($doc['status']) ?>">
                                    <?= $doc['status'] ?>
                                </span>
                            <?php else: ?>
                                <span class="badge" style="background:#f5f5f5;color:#888">Pending</span>
                            <?php endif; ?>
                        </td>
                        <td><?= $doc['authenticity_score'] ? $doc['authenticity_score'].'%' : '-' ?></td>
                    </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
            <?php else: ?>
                <p style="color:#888">No documents uploaded yet for this candidate.</p>
            <?php endif; ?>
        </div>
        <?php endif; ?>

    </div>
</div>
</body>
</html>
