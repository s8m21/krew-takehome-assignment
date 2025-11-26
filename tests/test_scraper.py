import unittest
from bs4 import BeautifulSoup
from scraper.extractor import extract_title, clean_text, extract_tags, build_ai_document
from scraper.utils import detect_language_simple, infer_content_type, estimate_reading_time, has_code_blocks

class TestExtractor(unittest.TestCase):
    def test_extract_title(self):
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(extract_title(soup), "Test Title")

        html_no_title = "<html><body><h1>Header Title</h1></body></html>"
        soup = BeautifulSoup(html_no_title, "html.parser")
        self.assertEqual(extract_title(soup), "Header Title")

    def test_clean_text(self):
        text = "  This   is  a   test.  "
        self.assertEqual(clean_text(text), "This is a test.")

    def test_extract_tags(self):
        html = """
        <html>
            <body>
                <a href="/tag/foo" class="tag">Foo</a>
                <a href="/tag/bar">Bar</a>
                <a href="/other">Other</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        tags = extract_tags(soup, "example.com")
        self.assertEqual(tags, ["bar", "foo"])

class TestUtils(unittest.TestCase):
    def test_detect_language(self):
        self.assertEqual(detect_language_simple("This is the test of the code."), "en")
        self.assertEqual(detect_language_simple("Hola mundo."), "unknown")

    def test_infer_content_type(self):
        self.assertEqual(infer_content_type("http://example.com/tag/foo", ""), "tag_page")
        self.assertEqual(infer_content_type("http://example.com/article", "word " * 100), "article")
        self.assertEqual(infer_content_type("http://example.com/short", "word " * 10), "short_form")

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
