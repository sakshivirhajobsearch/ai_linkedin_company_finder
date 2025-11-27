import requests
from bs4 import BeautifulSoup

def search_company(company_name):
    query = company_name.replace(" ", "%20")
    url = f"https://www.linkedin.com/search/results/companies/?keywords={query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        if "/company/" in a["href"]:
            full_link = "https://www.linkedin.com" + a["href"].split("?")[0]
            if full_link not in links:
                links.append(full_link)

    return links[:3]   # top 3 results
