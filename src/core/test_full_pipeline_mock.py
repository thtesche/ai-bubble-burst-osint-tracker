import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fetchers.market import MarketDataFetcher
from src.core.engine import ScoringEngine

# Mocking the web_extract tool for testing purposes
def mock_web_extract(urls):
    print(f"[*] [MOCK] web_extract called for: {urls}")
    # Simulate Google Finance Markdown content
    return {
        "results": [
            {
                "url": urls[0],
                "content": "Google Finance: NVDA is trading at $125.50. It has seen significant movement today."
            }
        ]
    }

def test_full_pipeline_with_mock():
    print("=== Testing Full Pipeline (Mocked Web Extract) ===")
    
    # 1. Setup
    tickers = ["NVDA"]
    market_fetcher = MarketDataFetcher(tickers)
    engine = ScoringEngine()

    # 2. Mock News (Sentiment side)
    mock_news_contents = [
        "AI is seeing massive exponential growth and revolutionary breakthroughs.",
        "The market shows signs of extreme speculation."
    ]

    # 3. Fetch Market Data (using the mock function)
    print("[*] Step 1: Fetching market data via Mock...")
    market_metrics = market_fetcher.fetch_market_metrics(web_extract_func=mock_web_extract)
    
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
    print("\n[+] Full Pipeline Integration Test (MOCK) passed!")

if __name__ == "__main__":
    try:
        test_full_pipeline_with_mock()
    except Exception as e:
        print(f"\n[!] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
