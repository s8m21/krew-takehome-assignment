# AI Scraping Pipeline Design

This project implements a small, production-minded scraping pipeline that collects documents from a single public website and converts them into AI-ready JSON objects suitable for search, RAG, fine-tuning, and analytics.

## Site Chosen

For demonstration, the scraper is configured to work well with [https://quotes.toscrape.com](https://quotes.toscrape.com), a sandbox site explicitly built for web scraping. The crawler is domain-agnostic and can be pointed at any single domain that allows scraping.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the scraper

```bash
python -m scraper.cli --start-url https://quotes.toscrape.com --max-pages 100 --output output.jsonl
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

### 5. Run with Docker

Build the image:
```bash
docker build -t ai-scraper .
```

Run the scraper:
```bash
docker run --rm -v "$(pwd)/output:/app/output" ai-scraper --start-url https://quotes.toscrape.com --output /app/output/docker_output.jsonl
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
| `language` | string | Detected language code (e.g., "en"). |
| `content_type` | string | Inferred type (e.g., "article", "tag_page"). |
| `fetched_at` | string | ISO 8601 timestamp of fetch. |
| `tags` | list[str] | Extracted tags/keywords. |
| `source_domain` | string | Domain of the source URL. |
| `reading_time_minutes` | float | Estimated reading time. |
| `quality_flags` | dict | Flags for potential quality issues (e.g., `too_short`). |

---

## Design Decisions

### Crawler
- **BFS Strategy**: Uses a queue to crawl pages in breadth-first order.
- **Politeness**: Implements a configurable delay between requests to avoid overwhelming the server.
- **Domain Restriction**: Strictly stays within the root domain of the start URL.
- **Deduplication**: Tracks visited URLs to prevent cycles and duplicate processing.

### Content Extraction
- **Heuristic Extraction**: Prioritizes semantic tags like `<article>` and `<main>`, falling back to the largest text block if necessary.
- **Cleaning**: Removes boilerplate (nav, footer, scripts) and normalizes whitespace to produce clean text for LLMs.

### Enrichment
- **Metadata**: Adds useful signals like word count and reading time to help with filtering and ranking.
- **Quality Flags**: explicitly flags documents that might be too short or missing titles, allowing downstream consumers to filter them out easily.

---

## Future Work

- **Distributed Crawling**: Use a task queue (e.g., Celery/Redis) for parallel crawling of large sites.
- **Respect robots.txt**: Parse and respect `robots.txt` rules.
- **Advanced Content Extraction**: Integrate libraries like `trafilatura` or `readability-lxml` for more robust extraction.
- **Vector Embeddings**: Compute embeddings (e.g., OpenAI, HuggingFace) during the pipeline and store them alongside the text.
- **Monitoring**: Add metrics (Prometheus) for crawl rate, error rates, and data quality.
