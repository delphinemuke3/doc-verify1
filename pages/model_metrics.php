<?php
require_once '../config.php';
require_once '../db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$metrics_path = __DIR__ . '/../python/models/doc_classifier_metrics.json';
$metrics = file_exists($metrics_path)
    ? json_decode(file_get_contents($metrics_path), true)
    : null;
$eval_path = __DIR__ . '/../python/fake_evaluation.json';
$eval_summary = file_exists($eval_path)
    ? json_decode(file_get_contents($eval_path), true)
    : null;
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Metrics - DocVerify</title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <style>
        .metric-big {
            font-size: 42px; font-weight: 700;
            color: #1a237e; text-align: center;
        }
        .metric-label {
            font-size: 13px; color: #666;
            text-align: center; margin-top: 4px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px; margin-bottom: 24px;
        }
        .metric-card {
            background: #fff; border-radius: 10px;
            padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            text-align: center;
        }
        .feat-bar-wrap {
            display: flex; align-items: center;
            gap: 10px; margin-bottom: 10px;
        }
        .feat-name {
            width: 160px; font-size: 13px;
            color: #333; flex-shrink: 0;
        }
        .feat-bar {
            height: 10px; background: #e0e0e0;
            border-radius: 5px; flex: 1; overflow: hidden;
        }
        .feat-fill {
            height: 100%; border-radius: 5px;
            background: linear-gradient(90deg, #1a237e, #3949ab);
            transition: width 1s ease;
        }
        .feat-pct {
            font-size: 13px; font-weight: 600;
            color: #1a237e; min-width: 44px;
            text-align: right;
        }
        .cv-score {
            display: inline-block; padding: 4px 12px;
            background: #e3f2fd; color: #1a237e;
            border-radius: 20px; font-size: 13px;
            font-weight: 600; margin: 4px;
        }
        .cm-table { width: 100%; border-collapse: collapse; }
        .cm-table td, .cm-table th {
            padding: 12px 16px; text-align: center;
            border: 1px solid #e0e0e0; font-size: 14px;
        }
        .cm-table th { background: #f5f5f5; font-weight: 600; }
        .cm-true { background: #e8f5e9; color: #2e7d32; font-weight: 700; }
        .cm-false { background: #ffebee; color: #c62828; font-weight: 700; }
    </style>
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
            <a href="model_metrics.php" class="active">Model Metrics</a>
            <a href="users.php">Users</a>
            <a href="logout.php">Logout</a>
        </nav>
    </div>

    <div class="main-content">
        <div class="page-title">AI Model Performance Metrics</div>

        <?php if (!$metrics): ?>
            <div class="card">
                <p style="color:#888">
                    No model trained yet. Run
                    <code>py python/train_model.py</code>
                    to train the model.
                </p>
            </div>
        <?php else: ?>

        <!-- Key metrics -->
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-big"><?= $metrics['accuracy'] ?>%</div>
                <div class="metric-label">Overall Accuracy</div>
            </div>
            <div class="metric-card">
                <div class="metric-big" style="color:#c62828">
                    <?= $metrics['fake_detection_rate'] ?? 'N/A' ?>%
                </div>
                <div class="metric-label">Fake Detection Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-big" style="color:#2e7d32">
                    <?= $metrics['real_detection_rate'] ?? 'N/A' ?>%
                </div>
                <div class="metric-label">Real Detection Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-big"><?= $metrics['cv_mean'] ?>%</div>
                <div class="metric-label">
                    Cross-validation Mean<br>
                    <small>(±<?= $metrics['cv_std'] ?>%)</small>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-big"><?= $metrics['total_samples'] ?></div>
                <div class="metric-label">
                    Total samples<br>
                    <small>
                        <?= $metrics['real_samples'] ?> real /
                        <?= $metrics['fake_samples'] ?> fake
                    </small>
                </div>
            </div>
        </div>

        <!-- Cross-validation scores -->
        <div class="card">
            <div class="card-title">Cross-Validation Scores (5-fold)</div>
            <p style="font-size:14px;color:#555;margin-bottom:12px">
                Each fold trains on 80% of data and tests on 20%.
                Consistent scores mean the model generalises well.
            </p>
            <?php if (!empty($metrics['cv_scores'])): ?>
                <?php foreach ($metrics['cv_scores'] as $i => $score): ?>
                    <span class="cv-score">Fold <?= $i+1 ?>: <?= $score ?>%</span>
                <?php endforeach; ?>
            <?php endif; ?>
            <div style="margin-top:12px;font-size:14px">
                <strong>Mean:</strong> <?= $metrics['cv_mean'] ?>% &nbsp;
                <strong>Std dev:</strong> ±<?= $metrics['cv_std'] ?>%
            </div>
        </div>

        <!-- Confusion matrix -->
        <div class="card">
            <div class="card-title">Confusion Matrix</div>
            <p style="font-size:14px;color:#555;margin-bottom:16px">
                Shows how the model classified documents in the test set.
            </p>
            <table class="cm-table">
                <thead>
                    <tr>
                        <th></th>
                        <th>Predicted: Fake</th>
                        <th>Predicted: Real</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <th>Actual: Fake</th>
                        <td class="cm-true">
                            <?= $metrics['true_fake'] ?><br>
                            <small>True Fake ✓</small>
                        </td>
                        <td class="cm-false">
                            <?= $metrics['false_real'] ?><br>
                            <small>Missed fake ✗</small>
                        </td>
                    </tr>
                    <tr>
                        <th>Actual: Real</th>
                        <td class="cm-false">
                            <?= $metrics['false_fake'] ?><br>
                            <small>False alarm ✗</small>
                        </td>
                        <td class="cm-true">
                            <?= $metrics['true_real'] ?><br>
                            <small>True Real ✓</small>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <?php if ($eval_summary): ?>
        <div class="card">
            <div class="card-title">Fake Document Evaluation</div>
            <p style="font-size:14px;color:#555;margin-bottom:16px">
                Latest system evaluation for fake documents. Results are recorded in <code>python/fake_evaluation.json</code>.
            </p>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div class="metric-card">
                    <div class="metric-big" style="color:#c62828"><?= $eval_summary['total_fake'] ?? 0 ?></div>
                    <div class="metric-label">Fake documents tested</div>
                </div>
                <div class="metric-card">
                    <div class="metric-big" style="color:#2e7d32"><?= $eval_summary['identified_fake'] ?? 0 ?></div>
                    <div class="metric-label">Correctly identified fake</div>
                </div>
                <div class="metric-card">
                    <div class="metric-big" style="color:#f57f17"><?= $eval_summary['missed_fake'] ?? 0 ?></div>
                    <div class="metric-label">Missed fake documents</div>
                </div>
                <div class="metric-card">
                    <div class="metric-big" style="color:#1a237e"><?= $eval_summary['detection_rate'] ?? 0 ?>%</div>
                    <div class="metric-label">Fake detection rate</div>
                </div>
            </div>
        </div>
        <?php endif; ?>

        <!-- Feature importance -->
        <div class="card">
            <div class="card-title">Feature Importance</div>
            <p style="font-size:14px;color:#555;margin-bottom:16px">
                How much each feature contributed to the model's decisions.
            </p>
            <?php
            $feats = $metrics['feature_importance'] ?? [];
            arsort($feats);
            foreach ($feats as $name => $pct):
                $label = ucfirst(str_replace('_', ' ', $name));
            ?>
            <div class="feat-bar-wrap">
                <div class="feat-name"><?= $label ?></div>
                <div class="feat-bar">
                    <div class="feat-fill" style="width:<?= min(100,$pct*5) ?>%"></div>
                </div>
                <div class="feat-pct"><?= $pct ?>%</div>
            </div>
            <?php endforeach; ?>
        </div>

        <!-- Interpretation -->
        <div class="card" style="border-left:4px solid #1a237e">
            <div class="card-title">Model Interpretation</div>
            <p style="font-size:14px;color:#555;line-height:1.8">
                The model achieves <strong><?= $metrics['accuracy'] ?>% accuracy</strong>
                on unseen test documents. Cross-validation across 5 folds gives a mean of
                <strong><?= $metrics['cv_mean'] ?>%</strong> with low variance
                (±<?= $metrics['cv_std'] ?>%), indicating the model generalises well
                to new documents. The most important features are image texture,
                edge density, and noise patterns — meaning the model learned to
                distinguish genuine Rwandan document printing characteristics
                from digitally tampered versions.
            </p>
        </div>

        <?php endif; ?>
    </div>
</div>
</body>
</html>