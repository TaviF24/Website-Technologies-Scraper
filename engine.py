import sys
import requests
import bs4
import dns.resolver
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth.stealth import Stealth


def fetch(domain):
    result = {'http':{}, 'https':{}}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for protocol in ['https', 'http']:
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

        if protocol == 'https' and result['https'].get('error') is None:
            result['http'] = result['https'].copy()
            break

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

def matching_pattern(rule, static_data, headless_data):
    protocol_static = 'https'
    protocol_headless = 'https'

    if rule['type'] != 'dns':
        if static_data[protocol_static].get('error') is not None:
            protocol_static = 'http'
            if static_data[protocol_static].get('error') is not None:
                return False
        if headless_data[protocol_headless].get('error') is not None:
            protocol_headless = 'http'
            if headless_data[protocol_headless].get('error') is not None:
                return False

    match rule['type']:
        case 'html':
            if rule['pattern'].lower() in static_data[protocol_static][rule['type']].lower():
                return True
            if rule['pattern'].lower() in headless_data[protocol_headless]['rendered_html'].lower():
                return True
            return False
        case 'link':
            for l in static_data[protocol_static][rule['type']]:
                if rule['pattern'].lower() in l.lower():
                    return True
            for url in headless_data[protocol_headless]['network_requests']:
                if rule['pattern'].lower() in url.lower():
                    return True
            return False
        case 'final-url':
            if rule['pattern'].lower() in static_data[protocol_static][rule['type']].lower():
                return True
            return False
        case 'meta':
            for d in static_data[protocol_static]['meta']:
                meta_key = d.get('name') or d.get('property')
                if meta_key and meta_key.lower() == rule['key'].lower():
                    content = d.get('content', '')
                    if rule['pattern'].lower() in content.lower():
                        return True
            return False
        case 'cookie':
            for cookie in static_data[protocol_static]['cookie']:
                if rule['pattern'].lower() in cookie.lower():
                    return True
            for cookie in headless_data[protocol_headless].get('js_cookies', []):
                if rule['pattern'].lower() in cookie.lower():
                    return True
            return False
        case 'script':
            for script in static_data[protocol_static]['script']:
                if script and rule['pattern'].lower() in script.lower():
                    return True
            for url in headless_data[protocol_headless]['network_requests']:
                if rule['pattern'].lower() in url.lower():
                    return True
            return False
        case 'header':
            if static_data[protocol_static][rule['type']].get(rule['key']):
                if rule['pattern'].lower() in static_data[protocol_static][rule['type']][rule['key']].lower():
                    return True
            return False
        case 'dns':
            for k, records in static_data['dns'].items():
                if k == 'error':
                    continue
                for record in records:
                    if rule['pattern'].lower() in record.lower():
                        return True
            return False

        case 'rendered_html':
            if rule['pattern'].lower() in  headless_data[protocol_headless][rule['type']].lower():
                return True
            return False
        case 'window_properties':
            for prop in headless_data[protocol_headless]['window_properties']:
                if rule['pattern'].lower() in prop.lower():
                    return True
            return False
        case 'network_requests':
            for url in headless_data[protocol_headless]['network_requests']:
                if rule['pattern'].lower() in url.lower():
                    return True
            return False

        case _:
            return False

def detect(technology, fetched_data, headless_fetched_data):
    result = {}
    for tech in technology['technologies']:
        score = 0
        r = []
        for rule in tech['rules']:
            if matching_pattern(rule, fetched_data, headless_fetched_data):
                score += rule['weight']
                r = {'type' : rule['type'], 'weight' : rule['weight'], 'pattern' : rule['pattern']}
        if score >= tech['threshold']:
            r['threshold'] = tech['threshold']
            result[tech['name']] = r
    return result


def fetch_headless(domain):
    result = {
        'http': {
            'rendered_html': '',
            'network_requests': [],
            'window_properties': [],
            'error': None
        },
        'https': {
            'rendered_html': '',
            'network_requests': [],
            'window_properties': [],
            'error': None
        }
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for protocol in ['https', 'http']:
            url = f"{protocol}://{domain}"
            page = browser.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            page.on("request", lambda request, prot=protocol: result[prot]['network_requests'].append(request.url))

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                # page.goto(url, wait_until="load", timeout=15000)
            except PlaywrightTimeoutError:
                result[protocol]['error'] = 'timeout_but_extracted'
            except Exception as e:
                result[protocol]['error'] = str(e)
                page.close()
                continue

            try:
                page.wait_for_load_state('networkidle', 5000)
                # page.wait_for_timeout(2000)
            except:
                pass


            try:
                result[protocol]['rendered_html'] = page.content()
                result[protocol]['window_properties'] = page.evaluate("Object.keys(window)")
                result[protocol]['js_cookies'] = [c['name'] for c in page.context.cookies()]
            except Exception as e:
                try:
                    page.wait_for_timeout(1000)
                    result[protocol]['rendered_html'] = page.content()
                    result[protocol]['window_properties'] = page.evaluate("Object.keys(window)")
                    result[protocol]['js_cookies'] = [c['name'] for c in page.context.cookies()]
                except Exception as e2:
                    print(f"Failed to extract DOM/Window from {url}: {e2}")
            finally:
                page.close()

            if protocol == 'https' and result['https']['error'] is None:
                result['http'] = result['https'].copy()
                break
        browser.close()
    return result