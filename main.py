import engine
import pandas as pd

# domain = "cloudflare.com"
# domain = "techcrunch.com"
# domain = "freshoffthegrid.com"
# domain = "wordpress.com"
# domain = "yourfamilylines.com"

technologies_file = "technologies.json"

df = pd.read_parquet('domains.parquet')
domains = df['root_domain'].tolist()

technologies = engine.read_technology(technologies_file)

unique_found_tech = set()
for i, domain in enumerate(domains):
    if i == 100:
        break
    total, techs = engine.detect(technologies, engine.fetch(domain), engine.fetch_headless(domain))
    unique_found_tech.update(techs)
    print(i, domain, total)

print("All technologies detected:", len(unique_found_tech))

# print(unique_found_tech)
# data = engine.fetch_headless(domain)
# print(data['https']['network_requests'])
# print(engine.fetch(domain)['https']['script'])
# print(engine.fetch(domains[4])['https']['final-url'])
# engine.detect(engine.read_technology(technologies_file), engine.fetch(domains[11]))