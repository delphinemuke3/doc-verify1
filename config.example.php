<?php
// Copy this file to config.php and update the values for your environment.

define('DB_HOST', '127.0.0.1');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'doc_verify_db');

define('UPLOAD_DIR', __DIR__ . '/uploads/');
define('MODELS_DIR', __DIR__ . '/models/');

define('PYTHON_PATH', __DIR__ . '/.venv/Scripts/python.exe');
define('PYTHON_DETECT', __DIR__ . '/python/detect.py');
define('PYTHON_SMILEID', __DIR__ . '/python/smileid_check.py');
define('TESSERACT_PATH', 'C:/Program Files/Tesseract-OCR/tesseract.exe');
define('PYTHON_ENABLED', true);

define('SMILEID_PARTNER_ID', '');
define('SMILEID_API_KEY', '');
define('SMILEID_SERVER', '0');

define('DETECTION_CONFIDENCE', 60);
define('MIN_MODEL_CONFIDENCE', 60);

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
