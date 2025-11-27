# AI Scraping Pipeline Design

This project implements a small, production-minded scraping pipeline that collects documents from a single public website and converts them into AI-ready JSON objects suitable for search, RAG, fine-tuning, and analytics.

## Site Chosen

This scraper is configured to work with [https://books.toscrape.com](https://books.toscrape.com), a sandbox site explicitly designed for web scraping practice. This choice allows testing the pipeline without ethical concerns or legal risks.

The site offers the right balance of complexity for demonstrating production-ready scraping. It provides:
- **Structured metadata** (categories, ratings) that can be extracted as tags—perfect for demonstrating enrichment.
- **Multiple page types** (listing pages, category pages) that showcase content type inference.
- **Internal navigation** with breadcrumbs and pagination, which tests the crawler's ability to follow links intelligently.

It's not trivial (like a single static page), but it's also not overwhelming (like a massive e-commerce site). This allows focus on building a clean, maintainable pipeline rather than fighting with anti-bot measures or complex JavaScript rendering.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the scraper

```bash
python -m scraper.cli --start-url https://books.toscrape.com --max-pages 100 --output output.jsonl
```

**Arguments:**
- `--start-url`: Seed URL to start crawling from.
- `--max-pages`: Maximum number of pages to crawl (default: 100).
- `--output`: Path to output JSONL file.
- `--delay`: Delay in seconds between requests (default: 0.5).
- `--allowed-path-prefix`: Optional path prefix to restrict crawling (e.g., `/docs/`).
- `--log-level`: Logging level (default: INFO).

### 3. Run Tests

```bash
python -m unittest discover tests
```

### 4. Run Analytics

```bash
python analytics.py output.jsonl
```

**Example Outputs:**
- See [`test_results.txt`](test_results.txt) for example test output (all 9 tests passing).
- See [`analytics_results.txt`](analytics_results.txt) for example analytics output showing language distribution, content types, and extracted tags.

### 5. Run with Docker

Build the image:
```bash
docker build -t ai-scraper .
```

Run the scraper:
```bash
docker run --rm -v "$(pwd)/output:/app/output" ai-scraper --start-url https://books.toscrape.com --output /app/output/docker_output.jsonl
```

---

## Data Schema

Each line in the output JSONL file is a valid JSON object representing an "AI Document".

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique UUID for the document. |
| `url` | string | Source URL. |
| `title` | string | Page title. |
| `body_text` | string | Cleaned main content text. |
| `word_count` | int | Number of words in body text. |
| `char_count` | int | Number of characters in body text. |
| `language` | string | Detected language code (e.g., "en") using `langdetect`. |
| `content_type` | string | Inferred type (e.g., "article", "tag_page"). |
| `fetched_at` | string | ISO 8601 timestamp of fetch. |
| `tags` | list[str] | Extracted tags/keywords (e.g., category, star rating). |
| `source_domain` | string | Domain of the source URL. |
| `path` | string | URL path component. |
| `reading_time_minutes` | float | Estimated reading time. |
| `has_code_blocks` | bool | Whether the document contains code blocks. |
| `quality_flags` | dict | Flags for potential quality issues (e.g., `too_short`). |

---

## Design Decisions

### Crawler
- **BFS Strategy**: Uses a queue to crawl pages in breadth-first order.
- **Politeness**: Implements a configurable delay between requests to avoid overwhelming the server. The delay is enforced even on errors to prevent tight loops.
- **Domain Restriction**: Strictly stays within the root domain of the start URL.
- **Deduplication**: Tracks visited URLs before adding them to the queue to prevent cycles and duplicate processing.
- **Filtering**: Skips non-content pages like login, logout, and basket/cart pages.
- **Memory Efficiency**: Uses a generator pattern to stream documents to disk incrementally, allowing the scraper to handle millions of pages without running out of memory.

### Content Extraction
- **Heuristic Extraction**: Prioritizes semantic tags like `<article>` and `<main>`, falling back to the largest text block if necessary.
- **Cleaning**: Removes boilerplate (nav, footer, scripts) and normalizes whitespace to produce clean text for LLMs.
- **Tag Extraction**: Tailored for `books.toscrape.com`, extracting categories from breadcrumbs and star ratings from class names.

### Enrichment
- **Metadata**: Adds useful signals like word count, reading time, and code block detection to help with filtering and ranking.
- **Language Detection**: Uses the `langdetect` library for accurate, multi-language support (50+ languages) rather than simple heuristics.
- **Quality Flags**: Explicitly flags documents that might be too short or missing titles, allowing downstream consumers to filter them out easily.

### AI Workflow Support
The schema is designed to support common AI use cases:
- **Search/RAG**: `body_text` is clean and ready for embedding. `tags` and `content_type` enable filtering. `quality_flags` help exclude low-quality documents.
- **Fine-tuning**: `language` and `word_count` allow you to build balanced training sets.
- **Analytics**: `fetched_at`, `source_domain`, and `reading_time_minutes` enable temporal analysis and content profiling.

---

## Future Work

- **Distributed Crawling**: Use a task queue (e.g., Celery/Redis) for parallel crawling of large sites.
- **Respect robots.txt**: Parse and respect `robots.txt` rules.
- **Advanced Content Extraction**: Integrate libraries like `trafilatura` or `readability-lxml` for more robust extraction.
- **Vector Embeddings**: Compute embeddings (e.g., OpenAI, HuggingFace) during the pipeline and store them alongside the text.
- **Monitoring**: Add metrics (Prometheus) for crawl rate, error rates, and data quality.
- **Incremental Updates**: Track previously crawled URLs in a database to support incremental re-crawls and change detection.

