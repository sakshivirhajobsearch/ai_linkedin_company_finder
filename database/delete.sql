USE linkedin_career_ai;

-- Delete a valid company record
DELETE FROM valid_company_results
WHERE company_name = 'Infosys';

-- Delete old invalid entries
DELETE FROM invalid_company_results
WHERE ai_confidence < 0.2;
