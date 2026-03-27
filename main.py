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

for i, domain in enumerate(domains):
    if i == 50:
        break

    print(domain, engine.detect(technologies, engine.fetch(domain)))

# print(engine.fetch(domains[4])['https']['final-url'])
# engine.detect(engine.read_technology(technologies_file), engine.fetch(domains[11]))