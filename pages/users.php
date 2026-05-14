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

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim($_POST['name']);
    $email = trim($_POST['email']);
    $password = $_POST['password'];

    if (!$name || !$email || !$password) {
        $error = 'Name, email and password are required.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Please enter a valid email address.';
    } else {
        $check = $db->prepare("SELECT id FROM users WHERE email = ? LIMIT 1");
        $check->bind_param("s", $email);
        $check->execute();
        $check->store_result();

        if ($check->num_rows > 0) {
            $error = 'A user with this email already exists.';
        } else {
            $hash = password_hash($password, PASSWORD_DEFAULT);
            $stmt = $db->prepare("INSERT INTO users (name, email, password) VALUES (?, ?, ?)");
            $stmt->bind_param("sss", $name, $email, $hash);
            if ($stmt->execute()) {
                $success = 'HR user account created successfully.';
            } else {
                $error = 'Failed to create user account.';
            }
        }

        $check->close();
    }
}

$users = $db->query("SELECT id, name, email FROM users ORDER BY id DESC");
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Users - DocVerify</title>
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
            <a href="verifications.php">Verifications</a>
            <a href="model_metrics.php">Model Metrics</a>
            <a href="users.php" class="active">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <div class="main-content">
        <div class="page-title">HR User Management</div>

        <?php if ($success): ?>
            <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
        <?php endif; ?>
        <?php if ($error): ?>
            <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>

        <div class="card">
            <div class="card-title">Register New HR User</div>
            <form method="POST">
                <div class="form-group">
                    <label for="name">Full Name *</label>
                    <input type="text" id="name" name="name" placeholder="e.g. Alice Uwase" required>
                </div>
                <div class="form-group">
                    <label for="email">Email Address *</label>
                    <input type="email" id="email" name="email" placeholder="e.g. alice@company.rw" required>
                </div>
                <div class="form-group">
                    <label for="password">Password *</label>
                    <input type="password" id="password" name="password" placeholder="Create a secure password" required>
                </div>
                <button type="submit" class="btn btn-primary btn-full">Create User</button>
            </form>
        </div>

        <div class="card">
            <div class="card-title">Existing HR Accounts</div>
            <?php if ($users && $users->num_rows > 0): ?>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Email</th>
                    </tr>
                </thead>
                <tbody>
                <?php $i = 1; while ($row = $users->fetch_assoc()): ?>
                    <tr>
                        <td><?= $i++ ?></td>
                        <td><?= htmlspecialchars($row['name']) ?></td>
                        <td><?= htmlspecialchars($row['email']) ?></td>
                    </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
            <?php else: ?>
                <p style="color:#888">No additional HR users have been added yet.</p>
            <?php endif; ?>
        </div>
    </div>
</div>
</body>
</html>
