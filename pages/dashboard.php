<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$db = getDB();

// Safe query helper — returns 0 if query fails
function safeCount($db, $sql) {
    $res = $db->query($sql);
    if (!$res) return 0;
    $row = $res->fetch_assoc();
    return $row ? (int)$row['cnt'] : 0;
}

$total_candidates = safeCount($db, "SELECT COUNT(*) as cnt FROM candidates");
$total_docs       = safeCount($db, "SELECT COUNT(*) as cnt FROM documents");
$verified         = safeCount($db, "SELECT COUNT(*) as cnt FROM verifications WHERE status='Verified'");
$fake             = safeCount($db, "SELECT COUNT(*) as cnt FROM verifications WHERE status='Fake'");
$suspicious       = safeCount($db, "SELECT COUNT(*) as cnt FROM verifications WHERE status='Suspicious'");

// Get recent candidates — safe check
$recent     = $db->query("SELECT c.*, v.status FROM candidates c 
    LEFT JOIN verifications v ON c.id = v.candidate_id 
    ORDER BY c.created_at DESC LIMIT 5");
$has_recent = ($recent && $recent->num_rows > 0);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<div class="main-layout">

    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-logo">Doc<span>Verify</span></div>
        <nav class="sidebar-nav">
            <a href="dashboard.php" class="active">Dashboard</a>
            <a href="candidates.php">Candidates</a>
            <a href="upload.php">Upload Documents</a>
            <a href="verifications.php">Verifications</a>
            <a href="model_metrics.php">Model Metrics</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <!-- Main content -->
    <div class="main-content">
        <div class="page-title">Welcome, <?= htmlspecialchars($_SESSION['user_name']) ?></div>

        <!-- Stats -->
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-number"><?= $total_candidates ?></div>
                <div class="stat-label">Total Candidates</div>
            </div>
            <div class="stat-card">
                <div class="stat-number"><?= $total_docs ?></div>
                <div class="stat-label">Documents Uploaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color:#2e7d32"><?= $verified ?></div>
                <div class="stat-label">Verified</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color:#f57f17"><?= $suspicious ?></div>
                <div class="stat-label">Suspicious</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color:#c62828"><?= $fake ?></div>
                <div class="stat-label">Fake Detected</div>
            </div>
        </div>

        <!-- Recent candidates -->
        <div class="card">
            <div class="card-title">Recent Candidates</div>
            <?php if ($has_recent): ?>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Position Applied</th>
                        <th>Date Added</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                <?php while($row = $recent->fetch_assoc()): ?>
                    <tr>
                        <td><?= htmlspecialchars($row['full_name']) ?></td>
                        <td><?= htmlspecialchars($row['position_applied'] ?? '-') ?></td>
                        <td><?= date('M d, Y', strtotime($row['created_at'])) ?></td>
                        <td>
                            <?php if($row['status']): ?>
                                <span class="badge badge-<?= strtolower($row['status']) ?>">
                                    <?= $row['status'] ?>
                                </span>
                            <?php else: ?>
                                <span class="badge" style="background:#f5f5f5;color:#888">Pending</span>
                            <?php endif; ?>
                        </td>
                        <td>
                            <a href="upload.php?candidate_id=<?= $row['id'] ?>" class="btn btn-primary" style="padding:4px 12px;font-size:13px">Upload Docs</a>
                        </td>
                    </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
            <?php else: ?>
                <p style="color:#888">No candidates yet. <a href="candidates.php">Add your first candidate</a>.</p>
            <?php endif; ?>
        </div>

    </div>
</div>
</body>
</html>