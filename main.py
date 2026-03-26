import sys
import requests
import bs4
import dns.resolver
import json

def fetch(domain):
    result = {'http':{}, 'https':{}}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for protocol in ['http', 'https']:
        try:
            resp = requests.get(protocol + '://' + domain, headers=headers, timeout=5)
            result[protocol]['cookie'] = [cookie.name for cookie in resp.cookies]
            result[protocol]['html'] = resp.text
            result[protocol]['final-url'] = resp.url
            result[protocol]['status'] = resp.status_code
            result[protocol]['header'] = {k.lower(): v.lower() for k, v in resp.headers.items()}

            html_doc = bs4.BeautifulSoup(resp.text, "html.parser")
            result[protocol]['meta'] = [m.attrs for m in html_doc.find_all('meta')]
            result[protocol]['link'] = [l.get('href') for l in html_doc.find_all('link') if l.get('href')]
            result[protocol]['script'] = [s.get('src') for s in html_doc.find_all('script') if s.get('src')]
            result[protocol]['anchor'] = [a.get('href') for a in html_doc.find_all('a') if a.get('href')]

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

def read_technology(input_file):
    with open(input_file, 'r') as f:
        data_json = json.load(f)
    return data_json

def matching_pattern(rule, data):

    match rule['type']:
        case 'html':
            if rule['pattern'].lower() in data['https'][rule['type']].lower():
                return True
            return False
        case 'meta':
            for d in data['https']['meta']:
                meta_key = d.get('name') or d.get('property')
                if meta_key and meta_key.lower() == rule['key'].lower():
                    content = d.get('content', '')
                    if rule['pattern'].lower() in content.lower():
                        return True
            return False
        case 'cookie':
            for cookie in data['https']['cookie']:
                if rule['pattern'].lower() in cookie.lower():
                    return True
            return False
        case 'script':
            for script in data['https']['script']:
                if script and rule['pattern'].lower() in script.lower():
                    return True
            return False
        case 'header':
            if data['https'][rule['type']].get(rule['key']):
                if rule['pattern'].lower() in data['https'][rule['type']][rule['key']].lower():
                    return True
            return False
        case 'dns':
            for k, records in data['dns'].items():
                if k == 'error':
                    continue
                for record in records:
                    if rule['pattern'].lower() in record.lower():
                        return True
            return False
        case _:
            return False

def detection_engine(technology, fetched_data):
    for tech in technology['technologies']:
        score = 0
        for rule in tech['rules']:
            if matching_pattern(rule, fetched_data):
                score += rule['weight']
                print(tech['name'], rule['type'])
        if score >= tech['threshold']:
            print("Found technology: " + tech['name'] + " | Score: " + str(score))

# domain = "cloudflare.com"
# domain = "techcrunch.com"
domain = "freshoffthegrid.com"
# domain = "wordpress.com"
technologies_file = "technologies.json"




# print(fetch(domain)['https']['link'])
detection_engine(read_technology(technologies_file), fetch(domain))