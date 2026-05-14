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
$edit_candidate = null;

if (isset($_GET['dedupe']) && $_GET['dedupe'] === '1') {
    $db->begin_transaction();
    $dedupe_sql = "SELECT c1.id AS duplicate_id, MIN(c2.id) AS keeper_id
        FROM candidates c1
        JOIN candidates c2
          ON TRIM(LOWER(c1.full_name)) = TRIM(LOWER(c2.full_name))
         AND IFNULL(TRIM(LOWER(c1.email)), '') = IFNULL(TRIM(LOWER(c2.email)), '')
         AND c1.id > c2.id
        GROUP BY c1.id";
    $duplicates = $db->query($dedupe_sql);

    // Safe check: query must succeed AND have rows
    if ($duplicates !== false && $duplicates->num_rows > 0) {
        $duplicate_ids = [];
        while ($row = $duplicates->fetch_assoc()) {
            $duplicate_id = (int)$row['duplicate_id'];
            $keeper_id = (int)$row['keeper_id'];
            $duplicate_ids[] = $duplicate_id;

            $db->query("UPDATE documents SET candidate_id = $keeper_id WHERE candidate_id = $duplicate_id");
            $db->query("UPDATE verifications SET candidate_id = $keeper_id WHERE candidate_id = $duplicate_id");
        }

        $ids_to_delete = implode(',', $duplicate_ids);
        $delete_sql = "DELETE FROM candidates WHERE id IN ($ids_to_delete)";

        if ($db->query($delete_sql) !== false) {
            $db->commit();
            $success = 'Duplicate candidates were removed successfully.';
        } else {
            $db->rollback();
            $error = 'Error removing duplicate candidates: ' . $db->error;
        }
    } else {
        $db->rollback();
        $success = 'No duplicate candidates found.';
    }
}

if (isset($_GET['delete']) && ctype_digit($_GET['delete'])) {
    $candidate_id = (int)$_GET['delete'];
    $db->begin_transaction();
    $delete_verifications = $db->prepare("DELETE FROM verifications WHERE candidate_id = ?");
    $delete_documents     = $db->prepare("DELETE FROM documents WHERE candidate_id = ?");
    $delete_candidate     = $db->prepare("DELETE FROM candidates WHERE id = ?");

    $delete_verifications->bind_param('i', $candidate_id);
    $delete_documents->bind_param('i', $candidate_id);
    $delete_candidate->bind_param('i', $candidate_id);

    if ($delete_verifications->execute() && $delete_documents->execute() && $delete_candidate->execute()) {
        $db->commit();
        $success = 'Candidate and associated documents were removed successfully.';
    } else {
        $db->rollback();
        $error = 'Error deleting candidate: ' . $db->error;
    }
}

if (isset($_GET['edit']) && ctype_digit($_GET['edit'])) {
    $edit_id = (int)$_GET['edit'];
    $stmt = $db->prepare("SELECT id, full_name, email, position_applied FROM candidates WHERE id = ?");
    $stmt->bind_param('i', $edit_id);
    $stmt->execute();
    $candidate_data = $stmt->get_result();
    // Safe check: result must be valid AND have exactly 1 row
    if ($candidate_data && $candidate_data->num_rows === 1) {
        $edit_candidate = $candidate_data->fetch_assoc();
    } else {
        $error = 'Candidate not found for editing.';
    }
}

// Handle add/edit candidate form
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $full_name    = trim($_POST['full_name'] ?? '');
    $email        = trim($_POST['email'] ?? '');
    $position     = trim($_POST['position_applied'] ?? '');
    $user_id      = $_SESSION['user_id'];
    $candidate_id = isset($_POST['candidate_id']) ? (int)$_POST['candidate_id'] : 0;

    if (empty($full_name)) {
        $error = 'Full name is required.';
    } else {
        if ($candidate_id > 0) {
            $check = $db->prepare(
                "SELECT id FROM candidates
                 WHERE LOWER(TRIM(full_name)) = LOWER(TRIM(?))
                   AND LOWER(TRIM(IFNULL(email, ''))) = LOWER(TRIM(?))
                   AND id != ?
                 LIMIT 1"
            );
            $check->bind_param("ssi", $full_name, $email, $candidate_id);
        } else {
            $check = $db->prepare(
                "SELECT id FROM candidates
                 WHERE LOWER(TRIM(full_name)) = LOWER(TRIM(?))
                   AND LOWER(TRIM(IFNULL(email, ''))) = LOWER(TRIM(?))"
            );
            $check->bind_param("ss", $full_name, $email);
        }

        $check->execute();
        $check->store_result();

        if ($check->num_rows > 0) {
            $error = 'A candidate with this name and email already exists.';
        } else {
            if ($candidate_id > 0) {
                $stmt = $db->prepare("UPDATE candidates SET full_name = ?, email = ?, position_applied = ? WHERE id = ?");
                $stmt->bind_param("sssi", $full_name, $email, $position, $candidate_id);
                if ($stmt->execute()) {
                    $success = 'Candidate updated successfully.';
                } else {
                    $error = 'Failed to update candidate.';
                }
            } else {
                $stmt = $db->prepare("INSERT INTO candidates (full_name, email, position_applied, created_by) VALUES (?, ?, ?, ?)");
                $stmt->bind_param("sssi", $full_name, $email, $position, $user_id);
                if ($stmt->execute()) {
                    $success = 'Candidate added successfully!';
                } else {
                    $error = 'Failed to add candidate.';
                }
            }
        }
        $check->close();
    }
}

// Get all candidates — safe check
$candidates     = $db->query("SELECT c.*, v.status FROM candidates c 
    LEFT JOIN verifications v ON c.id = v.candidate_id 
    ORDER BY c.created_at DESC");
$has_candidates = ($candidates && $candidates->num_rows > 0);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Candidates - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<div class="main-layout">

    <div class="sidebar">
        <div class="sidebar-logo">Doc<span>Verify</span></div>
        <nav class="sidebar-nav">
            <a href="dashboard.php">Dashboard</a>
            <a href="candidates.php" class="active">Candidates</a>
            <a href="upload.php">Upload Documents</a>
            <a href="verifications.php">Verifications</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <div class="main-content">
        <div class="page-title">Candidates</div>
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px">
            <a href="?dedupe=1" class="btn btn-warning" style="padding:10px 16px;">Remove Duplicate Candidates</a>
            <span style="color:#666;font-size:14px;">Use this when duplicate names like Delphine appear more than once.</span>
        </div>

        <?php if ($success): ?>
            <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
        <?php endif; ?>
        <?php if ($error): ?>
            <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>

        <!-- Add/Edit candidate form -->
        <div class="card">
            <div class="card-title"><?= $edit_candidate ? 'Edit Candidate' : 'Add New Candidate' ?></div>
            <form method="POST" action="candidates.php<?= $edit_candidate ? '?edit=' . $edit_candidate['id'] : '' ?>">
                <input type="hidden" name="candidate_id" value="<?= $edit_candidate ? $edit_candidate['id'] : 0 ?>">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
                    <div class="form-group">
                        <label>Full Name *</label>
                        <input type="text" name="full_name" required placeholder="e.g. Jean Claude Habimana"
                               value="<?= htmlspecialchars($edit_candidate['full_name'] ?? ($_POST['full_name'] ?? '')) ?>">
                    </div>
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" name="email" placeholder="e.g. jean@gmail.com"
                               value="<?= htmlspecialchars($edit_candidate['email'] ?? ($_POST['email'] ?? '')) ?>">
                    </div>
                    <div class="form-group">
                        <label>Position Applied</label>
                        <input type="text" name="position_applied" placeholder="e.g. Software Engineer"
                               value="<?= htmlspecialchars($edit_candidate['position_applied'] ?? ($_POST['position_applied'] ?? '')) ?>">
                    </div>
                </div>
                <button type="submit" class="btn btn-primary"><?= $edit_candidate ? 'Update Candidate' : 'Add Candidate' ?></button>
                <?php if ($edit_candidate): ?>
                    <a href="candidates.php" class="btn btn-secondary" style="margin-left:12px">Cancel</a>
                <?php endif; ?>
            </form>
        </div>

        <!-- Candidates table -->
        <div class="card">
            <div class="card-title">All Candidates</div>
            <?php if ($has_candidates): ?>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Full Name</th>
                        <th>Email</th>
                        <th>Position Applied</th>
                        <th>Date Added</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                <?php $i = 1; while($row = $candidates->fetch_assoc()): ?>
                    <tr>
                        <td><?= $i++ ?></td>
                        <td><?= htmlspecialchars($row['full_name']) ?></td>
                        <td><?= htmlspecialchars($row['email'] ?? '-') ?></td>
                        <td><?= htmlspecialchars($row['position_applied'] ?? '-') ?></td>
                        <td><?= date('M d, Y', strtotime($row['created_at'])) ?></td>
                        <td>
                            <?php if ($row['status']): ?>
                                <span class="badge badge-<?= strtolower($row['status']) ?>">
                                    <?= htmlspecialchars($row['status']) ?>
                                </span>
                            <?php else: ?>
                                <span class="badge" style="background:#f5f5f5;color:#888">Pending</span>
                            <?php endif; ?>
                        </td>
                        <td style="display:flex;flex-wrap:wrap;gap:8px">
                            <a href="candidates.php?edit=<?= $row['id'] ?>" class="btn btn-secondary" style="padding:4px 12px;font-size:13px">Edit</a>
                            <a href="candidates.php?delete=<?= $row['id'] ?>" class="btn btn-danger" style="padding:4px 12px;font-size:13px"
                               onclick="return confirm('Delete this candidate and all associated documents?');">Delete</a>
                            <a href="upload.php?candidate_id=<?= $row['id'] ?>" class="btn btn-primary" style="padding:4px 12px;font-size:13px">Upload Docs</a>
                            <a href="report.php?candidate_id=<?= $row['id'] ?>" class="btn btn-success" style="padding:4px 12px;font-size:13px">View Report</a>
                        </td>
                    </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
            <?php else: ?>
                <p style="color:#888">No candidates added yet.</p>
            <?php endif; ?>
        </div>

    </div>
</div>
</body>
</html>