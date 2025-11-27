import requests

def http_check(url):
    try:
        response = requests.get(url, timeout=8, allow_redirects=True)
        return response.status_code < 400, response.status_code
    except requests.exceptions.RequestException:
        return False, None
