import logging
import time
from collections import deque
from typing import Dict, Set, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .extractor import build_ai_document
from .utils import normalize_url, same_domain, should_skip_url
from .models import AIDocument

logger = logging.getLogger(__name__)


class SiteCrawler:
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        delay_seconds: float = 0.5,
        timeout: int = 10,
        allowed_path_prefix: Optional[str] = None,
        user_agent: str = "ai-collections-scraper/0.1",
    ):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.allowed_path_prefix = allowed_path_prefix

        parsed = urlparse(start_url)
        self.root_domain = parsed.netloc
        self.scheme = parsed.scheme

        self.headers = {"User-Agent": user_agent}

        self.visited: Set[str] = set()
        self.docs: List[AIDocument] = []

    def _within_allowed_path(self, url: str) -> bool:
        if not self.allowed_path_prefix:
            return True
        return urlparse(url).path.startswith(self.allowed_path_prefix)

    def _fetch_page(self, url: str) -> Optional[str]:
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning("Non-200 status %s for URL %s", resp.status_code, url)
                return None
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                # Skip non-HTML content
                logger.info("Skipping non-HTML content at %s", url)
                return None
            return resp.text
        except requests.RequestException as e:
            logger.warning("Request error for %s: %s", url, e)
            return None

    def _extract_links(self, base_url: str, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            normalized = normalize_url(base_url, href)
            links.append(normalized)
        return links

    def crawl(self) -> List[AIDocument]:
        queue = deque()
        queue.append(self.start_url)

        with tqdm(total=self.max_pages, desc="Crawling pages") as pbar:
            while queue and len(self.docs) < self.max_pages:
                url = queue.popleft()
                if url in self.visited:
                    continue
                if should_skip_url(url):
                    continue
                if not same_domain(url, self.root_domain):
                    continue
                if not self._within_allowed_path(url):
                    continue

                self.visited.add(url)

                html = self._fetch_page(url)
                if html is None:
                    continue

                # Build AI document
                try:
                    doc = build_ai_document(url, html)
                    self.docs.append(doc)
                except Exception as e:
                    logger.exception("Failed to build document for %s: %s", url, e)

                # Extract and enqueue links
                try:
                    links = self._extract_links(url, html)
                    for link in links:
                        if (
                            link not in self.visited
                            and same_domain(link, self.root_domain)
                            and not should_skip_url(link)
                            and self._within_allowed_path(link)
                        ):
                            queue.append(link)
                except Exception as e:
                    logger.exception("Failed to extract links from %s: %s", url, e)

                pbar.update(1)
                time.sleep(self.delay_seconds)

        return self.docs
