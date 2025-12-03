import logging
import time
from collections import deque
from typing import Dict, Set, List, Optional, Generator, Tuple
from urllib.parse import urlparse
import concurrent.futures
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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
        concurrency: int = 1,
        ignore_robots: bool = False,
    ):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.allowed_path_prefix = allowed_path_prefix
        self.user_agent = user_agent
        self.concurrency = concurrency
        self.ignore_robots = ignore_robots

        parsed = urlparse(start_url)
        self.root_domain = parsed.netloc
        self.scheme = parsed.scheme
        self.base_url = f"{self.scheme}://{self.root_domain}"

        self.visited: Set[str] = set()
        self.docs: List[AIDocument] = []

        # Session setup with retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Robots.txt setup
        self.rp = RobotFileParser()
        if not self.ignore_robots:
            robots_url = f"{self.base_url}/robots.txt"
            logger.info("Checking robots.txt at %s", robots_url)
            try:
                self.rp.set_url(robots_url)
                self.rp.read()
            except Exception as e:
                logger.warning("Failed to fetch/parse robots.txt: %s. Assuming allow all.", e)
                self.rp.allow_all = True

    def _within_allowed_path(self, url: str) -> bool:
        if not self.allowed_path_prefix:
            return True
        return urlparse(url).path.startswith(self.allowed_path_prefix)

    def _is_allowed_by_robots(self, url: str) -> bool:
        if self.ignore_robots:
            return True
        try:
            return self.rp.can_fetch(self.user_agent, url)
        except Exception:
            return True

    def _fetch_page(self, url: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning("Non-200 status %s for URL %s", resp.status_code, url)
                return None
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
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

    def _process_url(self, url: str) -> Tuple[Optional[AIDocument], List[str]]:
        """
        Worker function to process a single URL.
        """
        # Throttling per thread
        time.sleep(self.delay_seconds)

        if not self._is_allowed_by_robots(url):
            logger.info("Blocked by robots.txt: %s", url)
            return None, []

        html = self._fetch_page(url)
        if html is None:
            return None, []

        doc = None
        try:
            doc = build_ai_document(url, html)
        except Exception as e:
            logger.exception("Failed to build document for %s: %s", url, e)

        links = []
        try:
            links = self._extract_links(url, html)
        except Exception as e:
            logger.exception("Failed to extract links from %s: %s", url, e)

        return doc, links

    def crawl(self) -> Generator[AIDocument, None, None]:
        queue = deque([self.start_url])
        self.visited.add(self.start_url)
        
        with tqdm(total=self.max_pages, desc="Crawling pages") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                futures = {}
                
                while (futures or queue) and len(self.docs) < self.max_pages:
                    # Fill the pool
                    while queue and len(futures) < self.concurrency:
                        if len(self.docs) + len(futures) >= self.max_pages:
                            break
                        
                        url = queue.popleft()
                        future = executor.submit(self._process_url, url)
                        futures[future] = url
                    
                    if not futures:
                        break
                        
                    # Wait for at least one to complete
                    done, _ = concurrent.futures.wait(
                        futures.keys(), 
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    
                    for future in done:
                        url = futures.pop(future)
                        try:
                            doc, new_links = future.result()
                            if doc:
                                self.docs.append(doc)
                                yield doc
                                pbar.update(1)
                            
                            for link in new_links:
                                if (
                                    link not in self.visited
                                    and same_domain(link, self.root_domain)
                                    and not should_skip_url(link)
                                    and self._within_allowed_path(link)
                                ):
                                    self.visited.add(link)
                                    queue.append(link)
                                    
                        except Exception as e:
                            logger.error("Unexpected error in worker for %s: %s", url, e)
