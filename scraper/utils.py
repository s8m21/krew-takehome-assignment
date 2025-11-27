import re
from urllib.parse import urlparse, urljoin, urldefrag
from langdetect import detect, LangDetectException


def normalize_url(base_url: str, link: str) -> str:
    """
    Join relative URLs, remove fragments, and normalize.
    """
    joined = urljoin(base_url, link)
    # Remove fragmented section of URL
    clean, _ = urldefrag(joined)
    return clean


def same_domain(url: str, root_domain: str) -> bool:
    """
    Check if url belongs to the same domain as root_domain.
    """
    parsed = urlparse(url)
    return parsed.netloc == root_domain


def should_skip_url(url: str) -> bool:
    """
    Heuristic filters for non-content URLs.
    You can extend this list as needed.
    """
    lowered = url.lower()
    skip_patterns = [
        "logout", "login", "signin", "signup", "search",
        "basket",   # BooksToScrape has a basket/cart page
        "mailto:", "javascript:",
    ]
    if any(p in lowered for p in skip_patterns):
        return True

    # Skip file types that aren't HTML
    if re.search(r"\.(pdf|jpg|jpeg|png|gif|svg|ico|css|js|zip|tar|gz|mp4|mp3)$", lowered):
        return True

    return False


def detect_language_simple(text: str) -> str:
    """
    Detect language using langdetect library.
    Falls back to 'unknown' if detection fails or text is too short.
    """
    if not text or len(text.strip()) < 3:
        return "unknown"
        
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def infer_content_type(url: str, text: str) -> str:
    """
    Rule-based content type inference.
    Adjust rules per site if needed.
    """
    path = urlparse(url).path.lower()
    if "/tag/" in path:
        return "tag_page"
    if "/author/" in path:
        return "profile_page"
    if len(text.split()) < 50:
        return "short_form"
    return "article"


def estimate_reading_time(word_count: int, wpm: int = 200) -> float:
    return round(word_count / max(wpm, 1), 2)


def has_code_blocks(text: str) -> bool:
    """
    Simple heuristic for code documents.
    """
    patterns = [
        r"```",               # fenced code
        r"\bdef\b",           # Python
        r"\bclass\b",         # OOP
        r";\s*$",             # many languages
        r"\bfunction\b",      # JS
        r"public\s+static",   # Java/C#
    ]
    joined = "\n".join(text.splitlines()[:200])  # only first 200 lines
    return any(re.search(p, joined, re.MULTILINE) for p in patterns)
