<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$db = getDB();
$candidate_id = (int)($_GET['candidate_id'] ?? 0);

if (!$candidate_id) {
    header('Location: candidates.php');
    exit;
}

$candidate = $db->query("SELECT * FROM candidates WHERE id = $candidate_id")->fetch_assoc();
if (!$candidate) {
    header('Location: candidates.php');
    exit;
}

$verifications = $db->query("
    SELECT v.*, d.doc_type, d.file_path, d.uploaded_at
    FROM verifications v
    LEFT JOIN documents d ON v.document_id = d.id
    WHERE v.candidate_id = $candidate_id
    ORDER BY v.verified_at DESC
");

// Overall status: worst result wins
$overall_status = 'Verified';
$avg_score = 0;
$count = 0;
$rows = [];
while ($r = $verifications->fetch_assoc()) {
    $rows[] = $r;
    $avg_score += $r['authenticity_score'];
    $count++;
    if ($r['status'] === 'Fake') $overall_status = 'Fake';
    elseif ($r['status'] === 'Suspicious' && $overall_status !== 'Fake') $overall_status = 'Suspicious';
}
$avg_score = $count > 0 ? round($avg_score / $count) : 0;
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Report - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <style>
        .report-header {
            background: #1a237e;
            color: #fff;
            padding: 28px 32px;
            border-radius: 10px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .report-header h2 { font-size: 22px; margin-bottom: 4px; }
        .report-header p  { font-size: 14px; opacity: 0.8; margin: 2px 0; }
        .big-score {
            font-size: 52px;
            font-weight: 700;
            text-align: center;
            line-height: 1;
        }
        .big-status { font-size: 16px; text-align: center; opacity: 0.9; margin-top: 4px; }
        .doc-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .doc-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .doc-type { font-weight: 600; font-size: 15px; color: #1a237e; }
        .mini-bar {
            height: 6px; background: #eee;
            border-radius: 3px; flex: 1;
            margin: 0 10px; overflow: hidden;
        }
        .mini-fill { height: 100%; border-radius: 3px; background: #1a237e; }
        @media print {
            .sidebar, .no-print { display: none !important; }
            .main-content { padding: 0 !important; }
            .main-layout { display: block !important; }
        }
    </style>
</head>
<body>
<div class="main-layout">
    <div class="sidebar no-print">
        <div class="sidebar-logo">Doc<span>Verify</span></div>
        <nav class="sidebar-nav">
            <a href="dashboard.php">Dashboard</a>
            <a href="candidates.php">Candidates</a>
            <a href="upload.php">Upload Documents</a>
            <a href="verifications.php">Verifications</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <div class="main-content">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
            <div class="page-title" style="margin-bottom:0">Verification Report</div>
            <div class="no-print" style="display:flex;gap:10px">
                <button onclick="window.print()" class="btn btn-primary">Print / Save PDF</button>
                <a href="candidates.php" class="btn" style="background:#eee;color:#333">Back</a>
            </div>
        </div>

        <!-- Report header -->
        <div class="report-header">
            <div>
                <h2><?= htmlspecialchars($candidate['full_name']) ?></h2>
                <p>Position: <?= htmlspecialchars($candidate['position_applied'] ?? 'Not specified') ?></p>
                <p>Email: <?= htmlspecialchars($candidate['email'] ?? 'Not provided') ?></p>
                <p>Report generated: <?= date('F d, Y \a\t H:i') ?></p>
            </div>
            <div>
                <div class="big-score"><?= $avg_score ?>%</div>
                <div class="big-status"><?= $overall_status ?></div>
            </div>
        </div>

        <?php if (empty($rows)): ?>
            <div class="card">
                <p style="color:#888">No verifications found for this candidate.
                    <a href="upload.php?candidate_id=<?= $candidate_id ?>">Upload documents</a> to begin.
                </p>
            </div>
        <?php else: ?>

        <!-- Summary card -->
        <div class="card">
            <div class="card-title">Summary</div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;text-align:center">
                <div>
                    <div style="font-size:28px;font-weight:700;color:#1a237e"><?= $count ?></div>
                    <div style="font-size:13px;color:#666">Documents Checked</div>
                </div>
                <div>
                    <div style="font-size:28px;font-weight:700;color:#1a237e"><?= $avg_score ?>%</div>
                    <div style="font-size:13px;color:#666">Average Score</div>
                </div>
                <div>
                    <div style="font-size:28px;font-weight:700;
                        color:<?= $overall_status==='Verified'?'#2e7d32':($overall_status==='Suspicious'?'#f57f17':'#c62828') ?>">
                        <?= $overall_status ?>
                    </div>
                    <div style="font-size:13px;color:#666">Overall Status</div>
                </div>
            </div>
        </div>

        <!-- Per document results -->
        <div class="card">
            <div class="card-title">Document Results</div>
            <?php foreach($rows as $row): ?>
            <div class="doc-card">
                <div class="doc-card-header">
                    <span class="doc-type"><?= ucfirst(str_replace('_',' ',$row['doc_type'] ?? 'Document')) ?></span>
                    <span class="badge badge-<?= strtolower($row['status']) ?>"><?= $row['status'] ?></span>
                </div>
                <div style="display:flex;align-items:center;margin-bottom:10px">
                    <span style="font-size:13px;color:#666;width:60px">Score</span>
                    <div class="mini-bar">
                        <div class="mini-fill" style="width:<?= $row['authenticity_score'] ?>%"></div>
                    </div>
                    <span style="font-size:14px;font-weight:600"><?= $row['authenticity_score'] ?>%</span>
                </div>
                <?php if (!empty($row['issues'])): ?>
                <div style="margin-top:8px">
                    <div style="font-size:13px;font-weight:600;color:#555;margin-bottom:6px">Issues:</div>
                    <?php foreach(explode(';', $row['issues']) as $issue): ?>
                        <?php if(trim($issue)): ?>
                        <div style="font-size:13px;color:#f57f17;padding:4px 0">
                            &#9679; <?= htmlspecialchars(trim($issue)) ?>
                        </div>
                        <?php endif; ?>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
                <div style="margin-top:10px;font-size:13px;color:#555">
                    <strong>Recommendation:</strong> <?= htmlspecialchars($row['recommendation']) ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>

        <!-- Final recommendation -->
        <div class="card" style="border-left:4px solid <?= $overall_status==='Verified'?'#2e7d32':($overall_status==='Suspicious'?'#f57f17':'#c62828') ?>">
            <div class="card-title">Final Recommendation</div>
            <?php if ($overall_status === 'Verified'): ?>
                <p style="color:#2e7d32;font-size:15px">
                    All documents have passed verification. This candidate's credentials appear authentic.
                    You may proceed with the recruitment process.
                </p>
            <?php elseif ($overall_status === 'Suspicious'): ?>
                <p style="color:#f57f17;font-size:15px">
                    Some documents raised concerns. It is recommended to request original documents
                    and conduct a manual review before making a hiring decision.
                </p>
            <?php else: ?>
                <p style="color:#c62828;font-size:15px">
                    One or more documents show strong signs of forgery or tampering.
                    This application should be rejected and the case may be escalated for further investigation.
                </p>
            <?php endif; ?>
        </div>

        <?php endif; ?>
    </div>
</div>
</body>
</html>