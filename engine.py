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
        except dns.resolver.LifetimeTimeout:
            result['dns']['error'][record_type] = 'dns_error - timeout'
        except dns.resolver.NoNameservers:
            result['dns']['error'][record_type] = 'dns_error - no_nameservers'
        except Exception as e:
            result['dns']['error'][record_type] = f'dns_error - {str(e)}'
    return result

def read_technology(input_file):
    with open(input_file, 'r') as f:
        data_json = json.load(f)
    return data_json

def matching_pattern(rule, data):
    protocol = 'https'
    if rule['type'] != 'dns':
        if data[protocol].get('error') is not None:
            protocol = 'http'
            if data[protocol].get('error') is not None:
                return False

    match rule['type']:
        case 'html':
            if data[protocol][rule['type']].lower():
                return True
            return False
        case 'meta':
            for d in data[protocol]['meta']:
                meta_key = d.get('name') or d.get('property')
                if meta_key and meta_key.lower() == rule['key'].lower():
                    content = d.get('content', '')
                    if rule['pattern'].lower() in content.lower():
                        return True
            return False
        case 'cookie':
            for cookie in data[protocol]['cookie']:
                if rule['pattern'].lower() in cookie.lower():
                    return True
            return False
        case 'script':
            for script in data[protocol]['script']:
                if script and rule['pattern'].lower() in script.lower():
                    return True
            return False
        case 'header':
            if data[protocol][rule['type']].get(rule['key']):
                if rule['pattern'].lower() in data[protocol][rule['type']][rule['key']].lower():
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

def detect(technology, fetched_data):
    total = 0
    for tech in technology['technologies']:
        score = 0
        for rule in tech['rules']:
            if matching_pattern(rule, fetched_data):
                score += rule['weight']
                # print(tech['name'], rule['type'])
        if score >= tech['threshold']:
            total += 1
            # print("Found technology: " + tech['name'] + " | Score: " + str(score))
    return total