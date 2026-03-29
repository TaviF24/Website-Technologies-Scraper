import argparse
import json
import multiprocessing
import os
import engine
import pandas as pd
from rich.progress import track
from concurrent.futures import ProcessPoolExecutor, as_completed

def process_domain(args):
    domain, technologies_file = args
    technologies = engine.read_technology(technologies_file)
    static = engine.fetch(domain)
    headless = engine.fetch_headless(domain)
    techs = engine.detect(technologies, static, headless)
    return domain, techs


parser = argparse.ArgumentParser(description="Extract technologies from domains")
parser.add_argument('-if', '--input_file', metavar="FILE", help='input file with domains')
parser.add_argument('-tf', '--technologies_file', metavar="FILE", help='technologies json file')
parser.add_argument('-of', '--output_file', metavar="FILE", help='output file')
parser.add_argument('-p', '--processes', metavar="N", type=int, help='number of processes to use')
parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose output')
parser.add_argument("input", metavar="DOMAIN", help='domain', nargs='*')
args = parser.parse_args()
if not args.input_file and not args.input:
    parser.error("You must provide either --input_file or at least one INPUT domain")

technologies_file = args.technologies_file or "technologies.json"
domains = args.input or []

if args.input_file:
    extension = os.path.splitext(args.input_file)[1]
    match extension:
        case ".parquet":
            df = pd.read_parquet(args.input_file)
            if df is not None and len(df.columns) > 0:
                domains.extend(df[df.columns[0]].tolist())
        case ".txt":
            with open(args.input_file, "r") as f:
                lines = [line.strip().split() for line in f.readlines()]
                content = [domain for sublist in lines for domain in sublist]
                domains.extend(content)
        case _:
            parser.error("Invalid input file. Supported extensions are .parquet, .txt")

technologies = engine.read_technology(technologies_file)
unique_found_tech = set()
result = {}
max_workers = args.processes if args.processes else 4
args_list = [(domain, technologies_file) for domain in domains]
with ProcessPoolExecutor(max_workers=max_workers) as executor:
    futures = {executor.submit(process_domain, arg): arg[0] for arg in args_list}
    for future in track(as_completed(futures), total=len(futures), description="Processing..."):
        domain, techs = future.result()
        unique_found_tech.update(techs.keys())
        result[domain] = techs

print("Total different technologies detected:", len(unique_found_tech))

if args.output_file:
    output_file = args.output_file + ".json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=4)

for i, domain in enumerate(domains):
    # if i == 20:
    #     break
    print(f"\n{i + 1}. Found {len(result[domain])} technologies for {domain}",end='')
    if args.verbose:
        technologies = result[domain]
        print(f"\n🌐 Domain: {domain}")
        print("-" * (10 + len(domain)))
        for tech_name, details in technologies.items():
            print(f"  🔧 {tech_name}")
            for key, value in details.items():
                print(f"     - {key}: {value}")
print()


