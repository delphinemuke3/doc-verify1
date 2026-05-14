<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['done' => false]);
    exit;
}

$doc_id = (int)($_GET['doc_id'] ?? 0);
$db     = getDB();

$result = $db->query(
    "SELECT id FROM verifications WHERE document_id = $doc_id"
)->fetch_assoc();

echo json_encode(['done' => (bool)$result]);