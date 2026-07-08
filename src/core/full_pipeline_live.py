import sys
import os
import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.fetchers.news import NewsFetcher
from src.fetchers.market import MarketDataFetcher
from src.core.engine import ScoringEngine

# We no longer require hermes_tools as we use Firecrawl directly.

def e2e_test():
    print("=== STARTING REAL E2E TEST (LIVE DATA) ===")
    
    # 1. Setup
    engine = ScoringEngine()
    news_fetcher = NewsFetcher(query="AI bubble market news", limit=3)
    market_fetcher = MarketDataFetcher(tickers=["NVDA"])

    # 2. Real News Fetching
    print("\n[*] Step 1: Fetching REAL news via Firecrawl...")
    import asyncio
    news_contents = asyncio.run(news_fetcher.fetch_and_extract())
    
    if not news_contents:
        print("[!] ERROR: Failed to fetch real news. Pipeline aborted.")
        sys.exit(1)

    print(f"[+] Successfully fetched {len(news_contents)} real news articles.")
    for i, c in enumerate(news_contents):
        print(f"    Article {i+1} length: {len(c)} chars")

    # 3. Real Market Fetching
    print("\n[*] Step 2: Fetching REAL market data via Firecrawl...")
    market_metrics = market_fetcher.fetch_market_metrics()
    
    if not market_metrics or all(v['current_price'] == 0.0 for v in market_metrics.values()):
        print("[!] ERROR: Failed to fetch real market data or all prices are zero. Pipeline aborted.")
        sys.exit(1)

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
