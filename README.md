# AI Collections Scraper

This project implements a small, production-minded scraping pipeline that collects documents from a single public website and converts them into AI-ready JSON objects suitable for search, RAG, fine-tuning, and analytics.

## Site Chosen

For demonstration, the scraper is configured to work well with [https://quotes.toscrape.com](https://quotes.toscrape.com), a sandbox site explicitly built for web scraping. The crawler is domain-agnostic and can be pointed at any single domain that allows scraping.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
