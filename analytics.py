import json
import argparse
from collections import Counter
from statistics import mean

def analyze_output(file_path):
    print(f"Loading data from {file_path}...")
    
    docs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    docs.append(json.loads(line))
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return

    if not docs:
        print("No documents found.")
        return

    total_docs = len(docs)
    word_counts = [doc.get('word_count', 0) for doc in docs]
    avg_word_count = mean(word_counts) if word_counts else 0
    
    languages = [doc.get('language', 'unknown') for doc in docs]
    lang_dist = Counter(languages)
    
    content_types = [doc.get('content_type', 'unknown') for doc in docs]
    type_dist = Counter(content_types)

    print("\n--- Analysis Results ---")
    print(f"Total Documents: {total_docs}")
    print(f"Average Word Count: {avg_word_count:.2f}")
    
    print("\nLanguage Distribution:")
    for lang, count in lang_dist.items():
        print(f"  {lang}: {count} ({count/total_docs*100:.1f}%)")
        
    print("\nContent Type Distribution:")
    for ctype, count in type_dist.items():
        print(f"  {ctype}: {count} ({count/total_docs*100:.1f}%)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze scraped JSONL output.")
    parser.add_argument("file", help="Path to the JSONL output file.")
    args = parser.parse_args()
    
    analyze_output(args.file)
