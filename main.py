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

            html_doc = bs4.BeautifulSoup(resp.text, "html.parser")
            result[protocol]['meta'] = [m.attrs for m in html_doc.find_all('meta')]
            result[protocol]['links'] = [l.get('href') for l in html_doc.find_all('link') if l.get('href')]
            result[protocol]['scripts'] = [s.get('src') for s in html_doc.find_all('script') if s.get('src')]
            result[protocol]['anchors'] = [a.get('href') for a in html_doc.find_all('a') if a.get('href')]

        except requests.exceptions.Timeout:
            result[protocol]['error'] = 'timeout'
        except requests.exceptions.SSLError:
            result[protocol]['error'] = 'ssl_error'
        except requests.exceptions.ConnectionError:
            result[protocol]['error'] = 'connection_error'
        except:
            print("Unexpected error:", sys.exc_info()[0])

    result['dns'] = {'error' : {}}
    for record_type in ['A', 'CNAME', 'MX', 'TXT']:
        try:
            result['dns'][record_type] = [record.to_text() for record in dns.resolver.resolve(domain, record_type)]
        except dns.resolver.NoAnswer:
            result['dns']['error'][record_type] = 'dns_error - No Answer'
        except dns.resolver.NXDOMAIN:
            result['dns']['error'][record_type] = 'dns_error - NXDOMAIN'
    return result

domain = "google.com"
reqResult = requests.get("https://" + domain)



print(fetch(domain)['dns'])




