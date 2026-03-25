import sys
import requests
import bs4
import dns.resolver

def fetch(domain):
    result = {'http':{}, 'https':{}}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for protocol in ['http', 'https']:
        try:
            resp = requests.get(protocol + '://' + domain, headers=headers, timeout=5)
            result[protocol]['cookies'] = resp.cookies
            result[protocol]['html-body'] = resp.text
            result[protocol]['final-url'] = resp.url
            result[protocol]['status'] = resp.status_code
            result[protocol]['headers'] = resp.headers
        except requests.exceptions.Timeout:
            result[protocol]['error'] = 'timeout'
        except requests.exceptions.SSLError:
            result[protocol]['error'] = 'ssl_error'
        except requests.exceptions.ConnectionError:
            result[protocol]['error'] = 'connection_error'
        except:
            print("Unexpected error:", sys.exc_info()[0])
    return result


domain = "google.com"
reqResult = requests.get("https://" + domain)

html_doc = bs4.BeautifulSoup(reqResult.text, "html.parser")

print(fetch(domain))





