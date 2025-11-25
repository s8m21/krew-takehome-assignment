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

    return parser.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    crawler = SiteCrawler(
        start_url=args.start_url,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        allowed_path_prefix=args.allowed_path_prefix,
    )

    docs = crawler.crawl()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for doc in docs:
            json_line = json.dumps(doc.to_dict(), ensure_ascii=False)
            f.write(json_line + "\n")

    logging.info("Wrote %d documents to %s", len(docs), out_path)


if __name__ == "__main__":
    main()
