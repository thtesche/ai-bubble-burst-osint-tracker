import sys
import os

# Add src to path
project_root = "/Users/thtesche/VibeCoding/ai-bubble-burst-osint-tracker"
if project_root not in sys.path:
    sys.path.append(project_root)

from src.fetchers.news import NewsFetcher
from src.fetchers.market import MarketDataFetcher
from src.core.engine import ScoringEngine
from hermes_tools import web_extract, web_search

def e2e_test():
    print("=== STARTING REAL E2E TEST (LIVE DATA) ===")
    
    # 1. Setup
    engine = ScoringEngine()
    news_fetcher = NewsFetcher(query="AI bubble market news", limit=3)
    market_fetcher = MarketDataFetcher(tickers=["NVDA"])

    # 2. Real News Fetching
    print("\n[*] Step 1: Fetching REAL news via web_search/web_extract...")
    news_contents = news_fetcher.fetch_and_extract()
    
    if not news_contents:
        print("[!] Failed to fetch real news. Check web_search/web_extract availability.")
        return

    print(f"[+] Successfully fetched {len(news_contents)} real news articles.")
    for i, c in enumerate(news_contents):
        print(f"    Article {i+1} length: {len(c)} chars")

    # 3. Real Market Fetching
    print("\n[*] Step 2: Fetching REAL market data via Deep Search (Snippet + Extraction)...")
    # Pass BOTH web_search and web_extract to the fetcher
    market_metrics = market_fetcher.fetch_market_metrics(web_search_func=web_search, web_extract_func=web_extract)
    
    if not market_metrics:
        print("[!] Failed to fetch real market data.")
        return

    print(f"[+] Successfully fetched market metrics: {market_metrics}")

    # 4. Scoring
    print("\n[*] Step 3: Calculating REAL score...")
    sentiment_score = engine.analyze_sentiment(news_contents)
    market_score = market_fetcher.calculate_market_score(market_metrics)
    
    print(f"    Real Sentiment Score: {sentiment_score:.4f}")
    print(f"    Real Market Score:    {market_score:.4f}")

    final_bubble_score = engine.calculate_final_score(sentiment_score, market_score)
    print(f"\n[!!!] FINAL REAL BUBBLE SCORE: {final_bubble_score:.2f}%")
    print("=== E2E TEST COMPLETE ===")

if __name__ == "__main__":
    e2e_test()
