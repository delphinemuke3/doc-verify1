-- Run this in phpMyAdmin or MySQL console
-- Creates the database and tables needed for Doc Verify

CREATE DATABASE IF NOT EXISTS doc_verify_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE doc_verify_db;

-- Users table (HR staff who log in)
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','hr') DEFAULT 'hr',
    created_at DATETIME DEFAULT NOW()
);

-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    full_name        VARCHAR(200) NOT NULL,
    email            VARCHAR(150) DEFAULT NULL,
    position_applied VARCHAR(150) DEFAULT NULL,
    created_by       INT DEFAULT NULL,
    created_at       DATETIME DEFAULT NOW(),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Documents uploaded for candidates
CREATE TABLE IF NOT EXISTS documents (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT DEFAULT NULL,
    doc_type     VARCHAR(50) NOT NULL,
    file_path    VARCHAR(300) NOT NULL,
    uploaded_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL
);

-- Verifications table
CREATE TABLE IF NOT EXISTS verifications (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id       INT DEFAULT NULL,
    document_id        INT NOT NULL,
    authenticity_score INT DEFAULT 0,
    status             VARCHAR(20) DEFAULT 'Pending',
    issues             TEXT DEFAULT NULL,
    recommendation     TEXT DEFAULT NULL,
    verified_at        DATETIME DEFAULT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL,
    FOREIGN KEY (document_id)  REFERENCES documents(id) ON DELETE CASCADE
);

-- Default admin account (password: admin123)
INSERT INTO users (name, email, password, role) VALUES
('Admin', 'admin@docverify.rw', '$2y$10$VrllXrF4n2wZ3vHcoOJgqeMWIxtA2g9AzGI8tLLrpom5KAteoszyi', 'admin')
ON DUPLICATE KEY UPDATE id=id;
