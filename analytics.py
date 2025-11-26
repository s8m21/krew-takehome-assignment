"""
Simple analytics for the scraped JSONL output.

"""

import json
import argparse
from collections import Counter
from statistics import mean
from pathlib import Path


def load_documents(file_path):
    """Yield parsed JSON objects from a JSONL file, skipping blank/malformed lines."""
    p = Path(file_path)
    if not p.exists():
        print(f"Error: File {file_path} not found.")
        return

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # In a real system, you'd log this rather than print.
                print("Warning: Skipping malformed JSON line:", line[:80], "...")


def analyze_output(file_path: str) -> None:
    print(f"Loading data from {file_path}...")

    docs = list(load_documents(file_path))
    if not docs:
        print("No documents found.")
        return

    total_docs = len(docs)

    word_counts = [doc.get("word_count", 0) for doc in docs]
    avg_word_count = mean(word_counts) if word_counts else 0

    languages = [doc.get("language", "unknown") for doc in docs]
    lang_dist = Counter(languages)

    content_types = [doc.get("content_type", "unknown") for doc in docs]
    type_dist = Counter(content_types)

    tag_counter = Counter()
    for doc in docs:
        for tag in doc.get("tags", []):
            tag_counter[tag] += 1

    print("\n Analysis Results:")
    print(f"Total Documents: {total_docs}")
    print(f"Average Word Count: {avg_word_count:.2f}")

    print("\nLanguage Distribution:")
    for lang, count in lang_dist.most_common():
        pct = count / total_docs * 100
        print(f"  {lang}: {count} ({pct:.1f}%)")

    print("\nContent Type Distribution:")
    for ctype, count in type_dist.most_common():
        pct = count / total_docs * 100
        print(f"  {ctype}: {count} ({pct:.1f}%)")

    if tag_counter:
        print("\nTop Tags:")
        for tag, count in tag_counter.most_common(10):
            print(f"  {tag}: {count}")
    else:
        print("\nNo tags found.")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze scraped JSONL output."
    )
    parser.add_argument(
        "file",
        help="Path to the JSONL output file.",
    )
    args = parser.parse_args()

    analyze_output(args.file)

if __name__ == "__main__":
    main()

