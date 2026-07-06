import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fetchers.market import MarketDataFetcher
from src.core.engine import ScoringEngine

def test_full_pipeline_with_market():
    print("=== Testing Full Pipeline (News + Market) ===")
    
    # 1. Setup
    # Wir nutzen Nvidia und den S&P 500 als Indikatoren
    tickers = ["NVDA", "^GSPC"]
    market_fetcher = MarketDataFetcher(tickers)
    engine = ScoringEngine()

    # 2. Mock News (da wir im Test keine echten Web-Calls machen wollen, um die API zu schonen)
    # Aber wir simulieren den Output des NewsFetchers
    mock_news_contents = [
        "AI stocks are seeing massive volatility and extreme speculation.",
        "Investors are worried about the sustainability of AI growth.",
        "Tech sector shows signs of overheating."
    ]

    # 3. Fetch Market Data (Echte Daten via yfinance)
    print("[*] Step 1: Fetching real market data...")
    market_metrics = market_fetcher.fetch_market_metrics()
    
    if not market_metrics:
        print("[!] No market metrics fetched. Aborting.")
        return

    # 4. Calculate Scores
    print("[*] Step 2: Calculating scores...")
    sentiment_score = engine.analyze_sentiment(mock_news_contents)
    market_score = market_fetcher.calculate_market_score(market_metrics)
    
    print(f"    Sentiment Score: {sentiment_score:.4f}")
    print(f"    Market Score:    {market_score:.4f}")

    # 5. Final Result
    final_bubble_score = engine.calculate_final_score(sentiment_score, market_score)
    print(f"\n[+] FINAL BUBBLE SCORE: {final_bubble_score:.2f}%")

    # Assertions
    assert 0 <= final_bubble_score <= 100
    print("\n[+] Full Pipeline Integration Test passed!")

if __name__ == "__main__":
    try:
        test_full_pipeline_with_market()
    except Exception as e:
        print(f"\n[!] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
