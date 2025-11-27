import socket
import ssl

def get_domain(url):
    url = url.replace("https://", "").replace("http://", "")
    url = url.replace("www.", "")
    return url.split("/")[0]


def dns_check(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False

def ssl_check(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=6) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                ssock.getpeercert()
        return True
    except:
        return False
