import sys
import os

# Add project root (parent of src/) to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.fetchers.news import NewsFetcher
from src.fetchers.googlenews import GoogleNewsFetcher
from src.fetchers.market import MarketDataFetcher
from src.core.engine import ScoringEngine

def e2e_test():
    print("=== STARTING LIVE DATA ===")
    
    # 1. Setup
    engine = ScoringEngine()
    news_fetcher = NewsFetcher(query="Is the AI bubble about to burst", limit=10)
    googlenews_fetcher = GoogleNewsFetcher(
        query="Is the AI bubble about to burst", limit=10, use_firecrawl=False
    )
    market_fetcher = MarketDataFetcher(tickers=[
        "MSFT", "GOOGL", "AMZN", "META", "NVDA",
        "AMD", "ASML", "AVGO", "MU", "DELL",
        "SMCI", "HPE"
    ])

    # 2. Real News Fetching (Firecrawl)
    print("\n[*] Step 1: Fetching REAL news via Firecrawl...")
    import asyncio
    import json
    import os
    from datetime import datetime

    news_data = asyncio.run(news_fetcher.fetch_and_extract())
    
    if not news_data:
        print("[!] ERROR: Failed to fetch real news. Pipeline aborted.")
        sys.exit(1)

    # Save raw news to JSON for quality inspection
    # Wir berechnen den Root relativ zu dieser Datei (2 Ebenen hoch von src/core/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    actual_root = os.path.dirname(os.path.dirname(current_dir))
    log_dir = os.path.join(actual_root, "logs", "runs")
    
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    news_json_path = os.path.join(log_dir, f"news_raw_{timestamp}.json")
    
    with open(news_json_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, indent=4, ensure_ascii=False)
    print(f"[+] Raw news data saved to: {news_json_path}")

    # Extract contents for the scoring engine (which expects list[str])
    news_contents = [article['content'] for article in news_data]
    
    print(f"[+] Successfully fetched {len(news_contents)} real news articles.")
    for i, c in enumerate(news_contents):
        print(f"    Article {i+1} length: {len(c)} chars")

    # 2b. Google News Fetching (parallel)
    print("\n[*] Step 1b: Fetching REAL news via Google News RSS...")
    googlenews_data = googlenews_fetcher.fetch_articles_sync()
    
    googlenews_articles = googlenews_data.get("articles", [])
    googlenews_total = googlenews_data.get("total_results", 0)
    googlenews_contents = [
        a.get("content", a.get("description", ""))
        for a in googlenews_articles
    ]
    
    print(
        f"[+] Google News: {len(googlenews_articles)} articles "
        f"(total 24h results: {googlenews_total})"
    )
    
    # Google News Ergebnisse speichern
    googlenews_json_path = os.path.join(
        log_dir, f"googlenews_raw_{timestamp}.json"
    )
    with open(googlenews_json_path, "w", encoding="utf-8") as f:
        json.dump(googlenews_data, f, indent=4, ensure_ascii=False)
    print(f"[+] Google News data saved to: {googlenews_json_path}")
    
    # Contents für die Analyse zusammenführen
    all_news_contents = news_contents + googlenews_contents
    print(
        f"[+] Total news articles for analysis: "
        f"{len(all_news_contents)} "
        f"({len(news_contents)} Firecrawl + {len(googlenews_contents)} Google News)"
    )

    # 3. Real Market Fetching
    print("\n[*] Step 2: Fetching REAL market data via yfinance...")
    market_metrics = market_fetcher.fetch_market_metrics()

    if not market_metrics:
        print("[!] WARNING: No market data available. Continuing with news-only analysis.")
    else:
        print(f"[+] Successfully fetched market metrics: {market_metrics}")

    # 4. Scoring (mit combined news from both sources)
    print("\n[*] Step 3: Calculating REAL score...")
    sentiment_score = engine.analyze_sentiment(all_news_contents)
    market_score = market_fetcher.calculate_market_score(market_metrics)
    
    print(f"    Real Sentiment Score: {sentiment_score:.4f}")
    print(f"    Real Market Score:    {market_score:.4f}")
    
    final_bubble_score = engine.calculate_final_score(sentiment_score, market_score)
    print(f"\n[!!!] FINAL REAL BUBBLE SCORE: {final_bubble_score:.2f}%")
    print("=== E2E TEST COMPLETE ===")

if __name__ == "__main__":
    e2e_test()
