<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$doc_id       = (int)($_GET['doc_id'] ?? 0);
$candidate_id = (int)($_GET['candidate_id'] ?? 0);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verifying... - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <style>
        .verify-container {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            min-height: 80vh; text-align: center;
        }
        .spinner {
            width: 80px; height: 80px;
            border: 6px solid #e0e0e0;
            border-top: 6px solid #1a237e;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 24px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .step-list {
            list-style: none; padding: 0;
            margin: 24px 0; text-align: left;
        }
        .step-list li {
            padding: 8px 16px; margin-bottom: 8px;
            border-radius: 8px; font-size: 14px;
            background: #f5f5f5; color: #888;
            display: flex; align-items: center; gap: 10px;
            transition: all 0.3s;
        }
        .step-list li.active {
            background: #e3f2fd; color: #1a237e; font-weight: 600;
        }
        .step-list li.done {
            background: #e8f5e9; color: #2e7d32;
        }
        .step-icon { font-size: 16px; width: 20px; }
        .progress-line {
            width: 100%; max-width: 520px;
            height: 10px; background: #e8eaf6;
            border-radius: 999px; margin: 18px auto 8px;
            overflow: hidden;
        }
        .progress-fill {
            width: 0%; height: 100%; background: linear-gradient(90deg, #1a237e, #3949ab);
            transition: width 0.4s ease;
        }
        .progress-percent {
            color: #444; font-size: 13px; margin-bottom: 10px;
        }
    </style>
</head>
<body>
<div class="main-layout">
    <div class="sidebar">
        <div class="sidebar-logo">Doc<span>Verify</span></div>
        <nav class="sidebar-nav">
            <a href="dashboard.php">Dashboard</a>
            <a href="candidates.php">Candidates</a>
            <a href="upload.php" class="active">Upload Documents</a>
            <a href="verifications.php">Verifications</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>
    <div class="main-content">
        <div class="verify-container">
            <div class="spinner" id="spinner"></div>
            <h2 style="color:#1a237e;margin-bottom:8px">Verifying Document</h2>
            <p style="color:#666;font-size:14px">
                AI is analysing your document. Please wait...
            </p>

            <ul class="step-list" id="steps">
                <li id="step1"><span class="step-icon">⏳</span> Extracting text with OCR</li>
                <li id="step2"><span class="step-icon">⏳</span> Checking image integrity</li>
                <li id="step3"><span class="step-icon">⏳</span> Detecting face photo</li>
                <li id="step4"><span class="step-icon">⏳</span> Scanning for QR code</li>
                <li id="step5"><span class="step-icon">⏳</span> Running ML classifier</li>
                <li id="step6"><span class="step-icon">⏳</span> Cross-document consistency</li>
                <li id="step7"><span class="step-icon">⏳</span> Generating report</li>
            </ul>

            <div class="progress-line">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <p class="progress-percent" id="progress-percent">0% complete</p>
            <p style="color:#999;font-size:13px" id="status-msg">
                This usually takes 20-40 seconds...
            </p>
        </div>
    </div>
</div>

<script>
const steps = document.querySelectorAll('.step-list li');
const progressFill = document.getElementById('progress-fill');
const progressPercent = document.getElementById('progress-percent');
const statusMsg = document.getElementById('status-msg');
const totalSteps = steps.length;
let currentStep = 0;

function updateProgress(index) {
    const percent = Math.min(100, Math.round((index / totalSteps) * 100));
    progressFill.style.width = percent + '%';
    progressPercent.textContent = percent + '% complete';
}

function activateStep(i) {
    if (i > 0 && steps[i - 1]) {
        steps[i-1].classList.remove('active');
        steps[i-1].classList.add('done');
        steps[i-1].querySelector('.step-icon').textContent = '✓';
    }
    if (i < steps.length) {
        steps[i].classList.add('active');
        steps[i].querySelector('.step-icon').textContent = '🔄';
    }
    updateProgress(i);
}

activateStep(0);
const timings = [2500, 5500, 9500, 13500, 17000, 20500, 23500];
timings.forEach((t, i) => {
    setTimeout(() => {
        currentStep = i + 1;
        activateStep(i + 1);
        switch (i) {
            case 0: statusMsg.textContent = 'Extracting text and metadata...'; break;
            case 1: statusMsg.textContent = 'Inspecting the image quality...'; break;
            case 2: statusMsg.textContent = 'Detecting faces and identity markers...'; break;
            case 3: statusMsg.textContent = 'Scanning QR/security elements...'; break;
            case 4: statusMsg.textContent = 'Running AI classifier on document features...'; break;
            case 5: statusMsg.textContent = 'Checking cross-document consistency...'; break;
            case 6: statusMsg.textContent = 'Finalising report and recommendations...'; break;
        }
    }, t);
});

const docId = <?= $doc_id ?>;
const candId = <?= $candidate_id ?>;

function checkDone() {
    fetch(`check_verify.php?doc_id=${docId}`)
        .then(r => r.json())
        .then(data => {
            if (data.done) {
                steps.forEach(s => {
                    s.classList.remove('active');
                    s.classList.add('done');
                    s.querySelector('.step-icon').textContent = '✓';
                });
                updateProgress(totalSteps);
                document.getElementById('spinner').style.borderTopColor = '#2e7d32';
                statusMsg.textContent = 'Done! Redirecting to result page...';
                setTimeout(() => {
                    window.location.href =
                        `verify_result.php?doc_id=${docId}&candidate_id=${candId}`;
                }, 900);
            } else {
                setTimeout(checkDone, 3000);
            }
        })
        .catch(() => setTimeout(checkDone, 5000));
}

setTimeout(checkDone, 3000);
</script>
</body>
</html>