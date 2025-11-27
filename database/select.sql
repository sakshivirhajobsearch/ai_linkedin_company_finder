USE linkedin_career_ai;

-- All valid companies
SELECT * FROM valid_company_results;

-- All invalid companies
SELECT * FROM invalid_company_results;

-- Only strong cases
SELECT * FROM valid_company_results
WHERE ai_confidence >= 0.8;

-- Count summary
SELECT 
    (SELECT COUNT(*) FROM valid_company_results) AS total_valid,
    (SELECT COUNT(*) FROM invalid_company_results) AS total_invalid;
