<?php
require_once '../config.php';
require_once '../db.php';

if (isset($_SESSION['user_id'])) {
    header('Location: dashboard.php');
    exit;
}

$error = '';
$success = '';
$validToken = false;
$token = trim($_GET['token'] ?? '');

$db = getDB();

// Validate token
if ($token) {
    $stmt = $db->prepare("SELECT email FROM password_resets WHERE token = ? AND expires_at > NOW() AND used = 0 LIMIT 1");
    $stmt->bind_param("s", $token);
    $stmt->execute();
    $result = $stmt->get_result();
    $reset = $result->fetch_assoc();
    if ($reset) {
        $validToken = true;
    } else {
        $error = 'This reset link is invalid or has expired. Please request a new one.';
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $validToken) {
    $password = $_POST['password'];
    $confirm  = $_POST['confirm_password'];

    if (strlen($password) < 8) {
        $error = 'Password must be at least 8 characters.';
    } elseif ($password !== $confirm) {
        $error = 'Passwords do not match.';
    } else {
        $hashed = password_hash($password, PASSWORD_DEFAULT);

        // Update user password
        $upd = $db->prepare("UPDATE users SET password = ? WHERE email = ?");
        $upd->bind_param("ss", $hashed, $reset['email']);
        $upd->execute();

        // Mark token as used
        $mark = $db->prepare("UPDATE password_resets SET used = 1 WHERE token = ?");
        $mark->bind_param("s", $token);
        $mark->execute();

        $success = 'Your password has been reset. You can now sign in.';
        $validToken = false;
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Password - Doc Verify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body class="auth-page">
    <div class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <h1>Doc<span>Verify</span></h1>
                <p>Set a new password</p>
            </div>

            <?php if ($error): ?>
                <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <?php if ($success): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
                <div class="auth-links"><a href="login.php">← Sign In</a></div>
            <?php elseif ($validToken): ?>
            <form method="POST">
                <input type="hidden" name="token" value="<?= htmlspecialchars($token) ?>">
                <div class="form-group">
                    <label for="password">New Password</label>
                    <input type="password" id="password" name="password"
                           required placeholder="At least 8 characters">
                </div>
                <div class="form-group">
                    <label for="confirm_password">Confirm New Password</label>
                    <input type="password" id="confirm_password" name="confirm_password"
                           required placeholder="Repeat your new password">
                </div>
                <button type="submit" class="btn btn-primary btn-full">Reset Password</button>
            </form>
            <div class="auth-links"><a href="login.php">← Back to Sign In</a></div>
            <?php else: ?>
                <div class="auth-links"><a href="forgot_password.php">Request a new reset link</a></div>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>