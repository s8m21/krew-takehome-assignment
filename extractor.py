from bs4 import BeautifulSoup
from datetime import datetime
import re

def extract_content(soup: BeautifulSoup, url: str) -> dict:
    # Extract title
    title = soup.title.string.strip() if soup.title else ""
    # Extract main content (quotes)
    quotes = [q.get_text(strip=True) for q in soup.select(".quote .text")]
    body_text = "\n".join(quotes)
    # Extract tags (if any)
    tags = list({tag.get_text(strip=True) for tag in soup.select(".tag")})
    return {
        "title": title,
        "url": url,
        "body_text": clean_text(body_text),
        "tags": tags,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }

def clean_text(text: str) -> str:
    # Remove extra whitespace, normalize newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def enrich_document(doc: dict) -> dict:
    text = doc["body_text"]
    doc["word_count"] = len(text.split())
    doc["char_count"] = len(text)
    doc["language"] = "en"  # Heuristic: quotes.toscrape.com is English
    doc["content_type"] = "quote_page"
    return doc
