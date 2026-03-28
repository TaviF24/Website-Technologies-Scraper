import argparse
import os
import engine
import pandas as pd

parser = argparse.ArgumentParser(description="Extract technologies from domains")
parser.add_argument('-if', '--input_file', metavar="FILE", help='input file with domains')
parser.add_argument('-tf', '--technologies_file', metavar="FILE", help='technologies json file')
parser.add_argument('-lf', '--log_file', metavar="FILE", help='output log file')
parser.add_argument('-t', '--threads', metavar="N", help='number of threads to use')
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
for i, domain in enumerate(domains):
    if i == 5:
        break
    total, techs = engine.detect(technologies, engine.fetch(domain), engine.fetch_headless(domain))
    unique_found_tech.update(techs)
    print(i, domain, total)

print("All technologies detected:", len(unique_found_tech))