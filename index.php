<?php
require_once 'config.php';
if (isset($_SESSION['user_id'])) {
    header('Location: pages/dashboard.php');
    exit;
}
header('Location: pages/login.php');
exit;