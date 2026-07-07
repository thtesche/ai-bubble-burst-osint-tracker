import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fetchers.firecrawl_engine import FirecrawlEngine
from src.core.analyzer import BubbleAnalyzer

def main():
    print("==========================================")
    print("   🚀 AI BUBBLE BURST OSINT TRACKER       ")
    print("==========================================\n")

    SEARCH_QUERY = "AI market bubble burst risk analysis 2025 2026"
    LIMIT = 5

    engine = FirecrawlEngine(query=SEARCH_QUERY)
    analyzer = BubbleAnalyzer()

    print("[*] Starting direct Firecrawl API pipeline...")
    articles = engine.run_pipeline(limit=LIMIT)

    if not articles:
        print("[!] No data collected. Check if Atlantis is running and FIRECRAWL_BASE_URL is correct.")
        return

    print(f"[*] Processing {len(articles)} articles...")
    score, findings = analyzer.analyze_content(articles)
    report = analyzer.generate_report(score, findings)

    print("\n--- FINAL LIVE REPORT ---")
    print(report)
    print("\n==========================================")

if __name__ == '__main__':
    main()
