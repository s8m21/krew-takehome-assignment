from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List
import uuid
import re

from .models import AIDocument
from .utils import (
    detect_language_simple,
    infer_content_type,
    estimate_reading_time,
    has_code_blocks,
)


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    # fallback: first h1 or h2
    for tag in ["h1", "h2"]:
        el = soup.find(tag)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ""


def remove_unwanted_tags(soup: BeautifulSoup) -> None:
    """
    Remove nav, footer, script, style, and other boilerplate tags.
    """
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()


def find_main_content(soup: BeautifulSoup) -> str:
    """
    Heuristic: prefer <article> or <main>. If not found, choose the <div>
    with the largest amount of text.
    """
    # Prefer article / main if available
    for tag_name in ["article", "main"]:
        candidate = soup.find(tag_name)
        if candidate and candidate.get_text(strip=True):
            return candidate.get_text(separator="\n", strip=True)

    # Else pick the largest text block among divs
    best_div = None
    best_len = 0
    for div in soup.find_all("div"):
        text = div.get_text(separator="\n", strip=True)
        length = len(text)
        if length > best_len:
            best_len = length
            best_div = div

    if best_div:
        return best_div.get_text(separator="\n", strip=True)

    # fallback: whole page body text
    return soup.get_text(separator="\n", strip=True)


def clean_text(text: str) -> str:
    # collapse multiple whitespace/newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_tags(soup: BeautifulSoup, domain: str) -> List[str]:
    """
    Simple tag extraction for quotes.toscrape.com style pages:
    or more generally, look for common 'tag' patterns.
    """
    tags = set()
    # Example heuristic: links with 'tag' in class or href
    for a in soup.find_all("a"):
        classes = " ".join(a.get("class", []))
        href = a.get("href") or ""
        txt = a.get_text(strip=True)
        if "tag" in classes.lower() or "/tag/" in href.lower():
            if txt:
                tags.add(txt.lower())
    return sorted(tags)


def build_ai_document(url: str, html: str) -> AIDocument:
    soup = BeautifulSoup(html, "html.parser")

    remove_unwanted_tags(soup)
    title = extract_title(soup)
    raw_body = find_main_content(soup)
    body_text = clean_text(raw_body)

    # Enrichment
    word_count = len(body_text.split())
    char_count = len(body_text)
    language = detect_language_simple(body_text)
    content_type = infer_content_type(url, body_text)

    parsed = urlparse(url)
    source_domain = parsed.netloc
    path = parsed.path

    tags = extract_tags(soup, source_domain)
    reading_time_minutes = estimate_reading_time(word_count)
    code_blocks = has_code_blocks(body_text)

    quality_flags = {
        "too_short": word_count < 30,
        "too_long": word_count > 5000,
        "missing_title": len(title.strip()) == 0,
    }

    return AIDocument(
        id=str(uuid.uuid4()),
        url=url,
        title=title,
        body_text=body_text,
        word_count=word_count,
        char_count=char_count,
        language=language,
        content_type=content_type,
        fetched_at=AIDocument.now_iso(),
        tags=tags,
        source_domain=source_domain,
        path=path,
        reading_time_minutes=reading_time_minutes,
        has_code_blocks=code_blocks,
        quality_flags=quality_flags,
    )
