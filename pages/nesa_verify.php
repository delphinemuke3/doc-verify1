<?php
$serial = strtoupper(trim($_GET['serial'] ?? ''));
if (!preg_match('/^A\d{8}$/', $serial)) {
    http_response_code(400);
    echo 'Invalid NESA certificate number.';
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Opening NESA Verification</title>
</head>
<body>
    <form id="nesaForm" action="https://graduate.nesa.gov.rw/" method="post">
        <input type="hidden" name="serial" value="<?= htmlspecialchars($serial, ENT_QUOTES, 'UTF-8') ?>">
        <noscript>
            <p>Click verify to open the NESA certificate result.</p>
            <button type="submit">Verify</button>
        </noscript>
    </form>
    <script>
        document.getElementById('nesaForm').submit();
    </script>
</body>
</html>
