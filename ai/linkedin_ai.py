import re
from difflib import SequenceMatcher

def clean_text(text: str) -> str:
    text = text.lower().strip()

    # Remove common company noise
    noise_words = [
        "pvt", "ltd", "limited", "private",
        "corporation", "corp", "inc", "company"
    ]

    for word in noise_words:
        text = text.replace(word, "")

    text = re.sub(r"[^a-z0-9]", "", text)
    return text.strip()


def similarity_score(a: str, b: str) -> float:
    return round(SequenceMatcher(None, a, b).ratio(), 2)


def ai_confidence(company_name, linkedin_url):
    if not linkedin_url:
        return 0.0, "FAILED"

    clean_company = clean_text(company_name)

    # Extract slug from LinkedIn URL
    try:
        linkedin_slug = linkedin_url.split("/company/")[1].split("/")[0]
    except:
        return 0.3, "WEAK MATCH"

    clean_slug = clean_text(linkedin_slug)

    score = similarity_score(clean_company, clean_slug)

    if score > 0.8:
        verdict = "STRONG MATCH"
    elif score > 0.5:
        verdict = "WEAK MATCH"
    else:
        verdict = "FAILED"

    return score, verdict
