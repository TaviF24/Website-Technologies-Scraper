# Website-Technologies-Scraper

A Python-based tool for detecting technologies used by websites by combining classic HTTP scraping with headless browser analysis.

The project uses a large JSON dataset (1000+ technologies) where each technology is defined by detection rules (patterns, locations, and weights). The engine evaluates these rules against real website data and determines which technologies are present.

## 🚀 Overview

The project uses a dataset of **1000+ technologies**. Each technology is defined by specific detection rules including patterns, locations, and weights. The engine evaluates these rules against real-time website data to calculate a detection score.

### Rule Definition Example
Each technology is structured in JSON format:

```json
{
  "name": "Google Analytics",
  "category": "analytics",
  "threshold": 40,
  "rules": [
    {
      "type": "script",
      "pattern": "googletagmanager.com",
      "weight": 40
    },
    {
      "type": "html",
      "pattern": "gtag(",
      "weight": 20
    }
  ]
}
```
- rules define where and what to look for 
- weight contributes to a detection score
- threshold determines if the technology is considered detected

## ⚙️ How it works

The detection pipeline is split into three main steps:

### 1. Standard HTTP Fetch
The tool first performs a classic request-based scan:

- Fetches both https:// and http:// (prefers HTTPS)
- Extracts as much data as possible from the response

Some of the collected data includes:

- Response headers
- Status codes
- Final URL (after redirects)
- Cookies
- Raw HTML
- Meta tags
- Script sources (```<script src=...>```)
- Inline scripts
- Links (```<a>```, ```<link>```)
- DNS records (A, CNAME, MX, TXT)

This step is fast and provides a strong baseline for detection.

### 2. Headless Browser Fetch (Playwright)

Some technologies only appear after JavaScript execution. For this reason, the tool uses a headless browser.

This is important because many modern websites:

- Load content dynamically
- Inject scripts at runtime
- Use client-side rendering (React, Vue, etc.)
- Hide important signals from basic HTTP requests

Using a headless browser allows extraction of:

- Fully rendered HTML
- Network requests (very useful for analytics, CDNs, APIs)
- JavaScript window properties
- Cookies set via JavaScript

A stealth layer is also applied to reduce bot detection.


### 3. Detection Engine

Once all data is collected, the engine evaluates technologies:

- Iterates through every technology in the JSON file
- For each rule:
  - Checks if the relevant data type exists 
  - Searches for the pattern 
- If a match is found:
  - Adds the rule’s weight to the score

A technology is considered **detected** if:

```python 
total_score >= threshold 
```

Example logic:
```python
if score >= tech['threshold']:
    result[tech['name']] = matched_rules
```

The final result is a dictionary of detected technologies along with the rules that matched.

## 🧠 Detection Strategy

The system supports multiple rule types, such as:

- ```script``` → external JS sources
- ```html``` → raw HTML content
- ```header``` → HTTP headers
- ```cookie``` → cookies
- ```dns``` → DNS records
- ```network_requests``` → requests captured in the browser
- ```window_properties``` → global JS variables
- ```final-url``` → redirect targets

This layered approach improves accuracy and reduces false positives.

## 📊 Performance
- Supports multiprocessing (default: 4 processes)
- Designed to handle large domain lists efficiently

In testing:
- 200 domains scanned
- Up to 227 technologies detected

## 🤖 Technologies Dataset
- Contains 1000+ technologies
- Each with custom detection rules
- Generated with AI due to the scale and variability of patterns

## 🖥️ CLI Usage

The tool comes with a simple command-line interface:

```Bash 
python wtscraper.py [FLAGS] [DOMAIN ...]
```

### Arguments

| Flag                         | Description                                         |
|:-----------------------------|:----------------------------------------------------|
| `-h`, `--help`               | Show help message and exit                          |
| `-if`, `--input_file`        | File containing domains (.txt or .parquet formats)  |
| `-tf`, `--technologies_file` | Technologies JSON file (default: technologies.json) |
| `-of`, `--output_file`       | Output file where results will be saved             |
| `-p`, `--processes`          | Number of processes to use (default: 4)             |
| `-v`, `--verbose`            | Enable verbose output                               |
| `input`                      | One or more domains provided directly               |

### Examples

Scan two domains using your own technologies file (the format should be the same in order to work):

```Bash
python wtscraper.py -tf your_technologies_file.json example1.com example2.com 
```

Scan multiple domains from a file using more processes and put the result on results.json:

```Bash
python wtscraper.py -if domains.txt -of results -p 8
```

## ⚠️ Notes
- HTTPS is attempted first, with fallback to HTTP
- Some sites may block headless browsers despite stealth measures
- Detection accuracy depends on rule quality and coverage


## 💭 Debate Topics
### Main Issues with the Current Implementation

One issue is false positives. Some patterns are too generic and match content they shouldn’t. This can be improved by making patterns more specific and requiring stronger evidence before confirming a technology.

JavaScript-heavy websites are also tricky. Some content only appears after delays or user interaction, so a fixed waiting time isn’t always reliable. A smarter waiting strategy would improve detection.

Lastly, the technology dataset becomes outdated over time. Without a feedback loop, it’s hard to know when a detection rule stops working.

### Scaling to Millions of Domains in 1–2 Months

To scale, the system needs to become more distributed.

First, I would separate simple requests from headless browsing. Basic HTTP checks are fast and can run in parallel, while headless browsers are slower and should only be used when needed.

Then, I would use a queue-based system where domains are processed by multiple workers. This allows the system to scale easily by adding more machines.

For efficiency, I would also reuse browser instances instead of launching a new one for each domain.

Finally, running the system on cloud infrastructure makes it possible to process large volumes of domains within a reasonable time.

### Discovering New Technologies in the Future

Manually maintaining the dataset does not scale well.

A practical approach is to analyze the data already collected. If the same unknown scripts or domains appear across many websites, they are likely new technologies worth adding.

Another option is to follow industry sources like developer communities or product launch platforms to identify new tools early.

Public datasets can also help identify commonly used but unknown technologies.

In the long term, allowing community contributions would be the most effective way to keep the dataset updated.
