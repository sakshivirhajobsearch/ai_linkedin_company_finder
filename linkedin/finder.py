import re

def clean_company_slug(name: str) -> str:
    """
    Cleans company name into a LinkedIn-friendly slug.
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)  # remove symbols
    name = re.sub(r"\s+", "-", name)          # spaces -> dashes
    return name


def search_company(company_name: str) -> str | None:
    """
    Generates LinkedIn company URL safely.
    Keeps it simple and avoids fake strong AI matches.
    """
    try:
        slug = clean_company_slug(company_name)

        # Reject garbage names
        if len(slug) < 3 or "." in slug:
            return None

        return f"https://www.linkedin.com/company/{slug}/"
    except Exception:
        return None


def get_career_page(company_url: str | None) -> str | None:
    """
    Converts LinkedIn company page -> jobs page.
    """
    if not company_url:
        return None

    return company_url.rstrip("/") + "/jobs/"
