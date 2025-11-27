import re

def normalize_url(url):
    url = url.strip()

    # Remove existing protocol and www if present
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)

    # Remove trailing spaces
    url = url.strip()

    # Add forced format
    url = "https://www." + url

    return url
