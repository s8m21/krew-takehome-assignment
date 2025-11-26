"""
Unit tests for core scraper utilities and extractors.

Covers:
- Title extraction
- Text cleaning
- Tag extraction (BooksToScrape-style)
- Heuristic utils (language, content type, reading time, code detection)
- Basic smoke test for build_ai_document
"""

import unittest
from bs4 import BeautifulSoup

from scraper.extractor import (
    extract_title,
    clean_text,
    extract_tags,
    build_ai_document,
)
from scraper.utils import (
    detect_language_simple,
    infer_content_type,
    estimate_reading_time,
    has_code_blocks,
)


class TestExtractor(unittest.TestCase):
    def test_extract_title_prefers_html_title(self):
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        self.assertEqual(extract_title(soup), "Test Title")

    def test_extract_title_falls_back_to_heading(self):
        html_no_title = "<html><body><h1>Header Title</h1></body></html>"
        soup = BeautifulSoup(html_no_title, "html.parser")

        self.assertEqual(extract_title(soup), "Header Title")

    def test_clean_text_collapses_whitespace(self):
        text = "  This   is  a   test.  "
        self.assertEqual(clean_text(text), "This is a test.")

    def test_extract_tags_books_to_scrape_style(self):
        html = """
        <html>
          <body>
            <ul class="breadcrumb">
              <li><a href="/">Home</a></li>
              <li><a href="/catalogue/category/books_1/index.html">Books</a></li>
              <li class="active">Fiction</li>
            </ul>
            <p class="star-rating Three"></p>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        tags = extract_tags(soup, "books.toscrape.com")

        # Expect category + star rating tags
        self.assertEqual(tags, ["fiction", "three-star"])

    def test_build_ai_document_basic_fields(self):
        html = """
        <html>
          <head>
            <title>Sample Page</title>
          </head>
          <body>
            <div>
              <p>Hello world, this is a short test document.</p>
              <a href="/tag/test" class="tag">Test</a>
            </div>
          </body>
        </html>
        """
        url = "http://example.com/page"

        doc = build_ai_document(url, html)

        # Core fields
        self.assertEqual(doc.url, url)
        self.assertEqual(doc.title, "Sample Page")
        self.assertIn("Hello world", doc.body_text)
        self.assertGreater(doc.word_count, 0)
        self.assertGreater(doc.char_count, 0)

        # Enrichment
        self.assertEqual(doc.language, "en")
        self.assertEqual(doc.content_type, "short_form")  # < 50 words
        self.assertEqual(doc.source_domain, "example.com")
        self.assertEqual(doc.path, "/page")
        self.assertGreater(doc.reading_time_minutes, 0.0)

        # Tags: implementation-dependent, but should at least be a list
        self.assertIsInstance(doc.tags, list)

        # Quality signals
        self.assertIsInstance(doc.has_code_blocks, bool)
        self.assertIsInstance(doc.quality_flags, dict)


class TestUtils(unittest.TestCase):
    def test_detect_language_simple(self):
        self.assertEqual(
            detect_language_simple("This is the test of the code."),
            "en",
        )
        self.assertEqual(detect_language_simple("Hola mundo."), "unknown")

    def test_infer_content_type(self):
        self.assertEqual(
            infer_content_type("http://example.com/tag/foo", ""),
            "tag_page",
        )
        self.assertEqual(
            infer_content_type("http://example.com/article", "word " * 100),
            "article",
        )
        self.assertEqual(
            infer_content_type("http://example.com/short", "word " * 10),
            "short_form",
        )

    def test_estimate_reading_time(self):
        self.assertEqual(estimate_reading_time(200), 1.0)
        self.assertEqual(estimate_reading_time(100), 0.5)

    def test_has_code_blocks(self):
        code_text = "Here is some code:\n```python\ndef foo(): pass\n```"
        self.assertTrue(has_code_blocks(code_text))

        plain_text = "Just some plain text."
        self.assertFalse(has_code_blocks(plain_text))


if __name__ == "__main__":
    unittest.main()
