import argparse
import json
import logging
from pathlib import Path
from .crawler import SiteCrawler

def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape a website into AI-ready JSON documents."
    )
    parser.add_argument(
        "--start-url",
        required=True,
        help="Seed URL to start crawling from (must be on the target domain).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum number of pages to crawl.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output JSONL file.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between requests.",
    )
    parser.add_argument(
        "--allowed-path-prefix",
        default=None,
        help="Optional path prefix to restrict crawling (e.g., /docs/).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent workers (default: 1).",
    )
    parser.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Ignore robots.txt rules (default: False).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Configure logging with both file and console handlers
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8")
    ]

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers
    )

    crawler = SiteCrawler(
        start_url=args.start_url,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        allowed_path_prefix=args.allowed_path_prefix,
        concurrency=args.concurrency,
        ignore_robots=args.ignore_robots,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for doc in crawler.crawl():
            json_line = json.dumps(doc.to_dict(), ensure_ascii=False)
            f.write(json_line + "\n")
            count += 1

    logging.info("Wrote %d documents to %s", count, out_path)

if __name__ == "__main__":
    main()
