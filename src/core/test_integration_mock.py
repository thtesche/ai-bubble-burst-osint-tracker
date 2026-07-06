import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import ScoringEngine

def test_integration_mock():
    print("=== Testing Integration Mock (Fetcher -> Engine) ===")
    engine = ScoringEngine()

    # Simulated data that NewsFetcher.fetch_and_extract() would return
    mock_extracted_contents = [
        "AI is seeing massive exponential growth and revolutionary breakthroughs.",
        "The market shows signs of extreme speculation and potential bubble risks.",
        "Standard tech growth is observed in most sectors."
    ]

    print(f"[*] Mocked {len(mock_extracted_contents)} articles.")
    
    # 1. Test Sentiment Analysis on mock data
    print("[*] Step 1: Analyzing sentiment of mock data...")
    sentiment_score = engine.analyze_sentiment(mock_extracted_contents)
    print(f"    Sentiment Score: {sentiment_score:.4f}")

    # 2. Test Final Calculation
    print("[*] Step 2: Calculating final score with mock market data (0.5)...")
    market_score = 0.5
    final_score = engine.calculate_final_score(sentiment_score, market_score)
    print(f"    Final Bubble Score: {final_score:.2f}%")

    # Assertions
    assert 0 <= sentiment_score <= 1.0
    assert 0 <= final_score <= 100
    print("\n[+] Integration Mock passed!")

if __name__ == "__main__":
    try:
        test_integration_mock()
    except Exception as e:
        print(f"\n[!] Mock test failed: {e}")
        sys.exit(1)
