USE linkedin_career_ai;

-- ✅ INSERT VALID
INSERT INTO valid_company_results
(company_name, linkedin_company_page, linkedin_career_page,
 domain, dns_status, ssl_status, http_status,
 ai_confidence, ai_verdict)
VALUES
('Infosys', 'https://linkedin.com/company/infosys/',
 'https://linkedin.com/company/infosys/jobs/',
 'infosys.com', 1, 1, 200, 0.95, 'STRONG');

-- ❌ INSERT INVALID
INSERT INTO invalid_company_results
(company_name, linkedin_company_page, linkedin_career_page,
 domain, dns_status, ssl_status, http_status,
 ai_confidence, ai_verdict, failure_reason)
VALUES
('FakeCo', NULL, NULL,
 'fakeco.xyz', 0, 0, NULL, 0.2, 'FAILED', 'DNS+SSL FAILED');
