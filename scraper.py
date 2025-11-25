import argparse
import json
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from extractor import extract_content, enrich_document

VISITED = set()


def is_internal(url, domain):
    return urlparse(url).netloc == domain


def should_skip(url):
    # Skip login, search, etc. (customize as needed)
    return any(x in url for x in ["/login", "/search", "/signup"])


def crawl(start_url, max_pages):
    domain = urlparse(start_url).netloc
    to_visit = [start_url]
    docs = []
    while to_visit and len(VISITED) < max_pages:
        url = to_visit.pop(0)
        if url in VISITED or should_skip(url):
            continue
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            doc = extract_content(soup, url)
            doc = enrich_document(doc)
            docs.append(doc)
            VISITED.add(url)
            # Find new links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if is_internal(link, domain) and link not in VISITED and not should_skip(link):
                    to_visit.append(link)
            time.sleep(1)  # Throttle
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
    return docs


def main():
    parser = argparse.ArgumentParser(description="Scrape a website into AI-ready JSONL.")
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    docs = crawl(args.start_url, args.max_pages)
    with open(args.output, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    print(f"Scraped {len(docs)} documents.")

if __name__ == "__main__":
    main()
