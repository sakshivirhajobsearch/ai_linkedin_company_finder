import re

def clean_company_name(name):
    name = name.lower().strip()
    name = re.sub(r"(pvt ltd|private limited|ltd|limited|corp|corporation|inc)", "", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return name.strip()

def ai_match_score(input_name, linkedin_name):
    input_clean = clean_company_name(input_name)
    linkedin_clean = clean_company_name(linkedin_name)

    input_set = set(input_clean.split())
    linkedin_set = set(linkedin_clean.split())

    score = len(input_set.intersection(linkedin_set)) / max(len(input_set), 1)
    return round(score, 2)
