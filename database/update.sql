USE linkedin_career_ai;

-- Update AI confidence for a company
UPDATE valid_company_results
SET ai_confidence = 0.98,
    ai_verdict = 'STRONG'
WHERE company_name = 'Infosys';

-- Update failure reason
UPDATE invalid_company_results
SET failure_reason = 'Manual Override'
WHERE company_name = 'FakeCo';
