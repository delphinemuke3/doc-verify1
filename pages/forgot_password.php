<?php
require_once '../config.php';
require_once '../db.php';

if (isset($_SESSION['user_id'])) {
    header('Location: dashboard.php');
    exit;
}

$message = '';
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email']);

    $db = getDB();
    $stmt = $db->prepare("SELECT id, name FROM users WHERE email = ? LIMIT 1");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();
    $user = $result->fetch_assoc();

    if ($user) {
        // Generate a secure token
        $token = bin2hex(random_bytes(32));
        $expires = date('Y-m-d H:i:s', strtotime('+1 hour'));

        // Store token in DB (create this table if it doesn't exist)
        $db->query("CREATE TABLE IF NOT EXISTS password_resets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            token VARCHAR(64) NOT NULL,
            expires_at DATETIME NOT NULL,
            used TINYINT(1) DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )");

        // Delete any existing tokens for this email
        $del = $db->prepare("DELETE FROM password_resets WHERE email = ?");
        $del->bind_param("s", $email);
        $del->execute();

        // Insert new token
        $ins = $db->prepare("INSERT INTO password_resets (email, token, expires_at) VALUES (?, ?, ?)");
        $ins->bind_param("sss", $email, $token, $expires);
        $ins->execute();

        // Build reset link
        $resetLink = (isset($_SERVER['HTTPS']) ? 'https' : 'http') . '://' . $_SERVER['HTTP_HOST']
            . dirname($_SERVER['SCRIPT_NAME']) . '/reset_password.php?token=' . $token;

        // Send email using PHP mail() — replace with PHPMailer/SMTP for production
        $subject = "DocVerify – Password Reset";
        $body = "Hello {$user['name']},\n\nClick the link below to reset your password (valid for 1 hour):\n\n$resetLink\n\nIf you did not request this, ignore this email.\n\nDocVerify Team";
        $headers = "From: no-reply@docverify.rw\r\nContent-Type: text/plain; charset=UTF-8";
        mail($email, $subject, $body, $headers);

        // Always show success (don't reveal whether email exists)
        $message = 'If that email is registered, a password reset link has been sent. Check your inbox.';
    } else {
        // Same message to avoid user enumeration
        $message = 'If that email is registered, a password reset link has been sent. Check your inbox.';
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forgot Password - Doc Verify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body class="auth-page">
    <div class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <h1>Doc<span>Verify</span></h1>
                <p>Reset your password</p>
            </div>

            <?php if ($message): ?>
                <div class="alert alert-success"><?= htmlspecialchars($message) ?></div>
            <?php endif; ?>

            <?php if (!$message): ?>
            <form method="POST">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required
                           placeholder="Enter your registered email"
                           value="<?= htmlspecialchars($_POST['email'] ?? '') ?>">
                </div>
                <button type="submit" class="btn btn-primary btn-full">Send Reset Link</button>
            </form>
            <?php endif; ?>

            <div class="auth-links">
                <a href="login.php">← Back to Sign In</a>
            </div>
        </div>
    </div>
</body>
</html>