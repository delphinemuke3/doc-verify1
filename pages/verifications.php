<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$db = getDB();

// Safe query check
$results     = $db->query("
    SELECT v.*, c.full_name, c.position_applied, d.doc_type, d.file_path
    FROM verifications v
    JOIN candidates c ON v.candidate_id = c.id
    LEFT JOIN documents d ON v.document_id = d.id
    ORDER BY v.verified_at DESC
");
$has_results = ($results && $results->num_rows > 0);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verifications - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<div class="main-layout">
    <div class="sidebar">
        <div class="sidebar-logo">Doc<span>Verify</span></div>
        <nav class="sidebar-nav">
            <a href="dashboard.php">Dashboard</a>
            <a href="candidates.php">Candidates</a>
            <a href="upload.php">Upload Documents</a>
            <a href="verifications.php" class="active">Verifications</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <div class="main-content">
        <div class="page-title">All Verifications</div>

        <div class="card">
            <?php if ($has_results): ?>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Candidate</th>
                        <th>Position</th>
                        <th>Document Type</th>
                        <th>Score</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                <?php $i = 1; while($row = $results->fetch_assoc()): ?>
                    <tr>
                        <td><?= $i++ ?></td>
                        <td><?= htmlspecialchars($row['full_name']) ?></td>
                        <td><?= htmlspecialchars($row['position_applied'] ?? '-') ?></td>
                        <td><?= ucfirst(str_replace('_', ' ', $row['doc_type'] ?? '-')) ?></td>
                        <td><strong><?= $row['authenticity_score'] ?>%</strong></td>
                        <td>
                            <span class="badge badge-<?= strtolower($row['status']) ?>">
                                <?= htmlspecialchars($row['status']) ?>
                            </span>
                        </td>
                        <td>
                            <?php
                                $date = $row['verified_at'];
                                echo ($date && $date !== '0000-00-00 00:00:00')
                                    ? date('M d, Y', strtotime($date))
                                    : '-';
                            ?>
                        </td>
                        <td>
                            <a href="report.php?candidate_id=<?= $row['candidate_id'] ?>"
                               class="btn btn-success" style="padding:4px 12px;font-size:13px">
                               View Report
                            </a>
                        </td>
                    </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
            <?php else: ?>
                <p style="color:#888">No verifications yet.</p>
            <?php endif; ?>
        </div>
    </div>
</div>
</body>
</html>