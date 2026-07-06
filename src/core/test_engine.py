import sys
import os

# Add current directory to path for local imports
sys.path.append(os.getcwd())

try:
    from engine import ScoringEngine
except ImportError:
    # Fallback for different execution contexts
    from src.core.engine import ScoringEngine

def test_engine():
    engine = ScoringEngine()
    
    # Test 1: Neutraler Text
    neutral_text = ["The market is stable and showing steady growth in the tech sector."]
    score_neutral = engine.analyze_sentiment(neutral_text)
    print(f"Neutral Score: {score_neutral:.4f}")

    # Test 2: Hype-Text
    hype_text = ["Revolutionary breakthrough! Massive exponential growth and skyrocketing profits!"]
    score_hype = engine.analyze_sentiment(hype_text)
    print(f"Hype Score: {score_hype:.4f}")

    # Test 3: Kombination
    final = engine.calculate_final_score(score_hype, 0.5)
    print(f"Final Combined Score (Hype + Mid-Market): {final:.2f}%")

    # Assertions
    assert score_neutral < score_hype, "Hype score should be higher than neutral"
    assert 0 <= final <= 100, "Final score must be between 0 and 100"
    print("\n[+] Engine tests passed!")

if __name__ == "__main__":
    try:
        test_engine()
    except Exception as e:
        print(f"\n[!] Test failed: {e}")
        sys.exit(1)
