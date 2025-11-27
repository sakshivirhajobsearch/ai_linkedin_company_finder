CREATE DATABASE IF NOT EXISTS linkedin_career_ai;
USE linkedin_career_ai;

-- ================= VALID TABLE =================
CREATE TABLE IF NOT EXISTS valid_company_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255),
    linkedin_company_page TEXT,
    linkedin_career_page TEXT,
    domain VARCHAR(255),
    dns_status BOOLEAN,
    ssl_status BOOLEAN,
    http_status INT,
    ai_confidence FLOAT,
    ai_verdict VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================= INVALID TABLE =================
CREATE TABLE IF NOT EXISTS invalid_company_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255),
    linkedin_company_page TEXT,
    linkedin_career_page TEXT,
    domain VARCHAR(255),
    dns_status BOOLEAN,
    ssl_status BOOLEAN,
    http_status INT,
    ai_confidence FLOAT,
    ai_verdict VARCHAR(50),
    failure_reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
