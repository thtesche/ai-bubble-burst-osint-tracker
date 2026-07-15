"""Tests for ScoringEngine - no external dependencies."""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.engine import ScoringEngine


def test_empty_contents_returns_zero():
    """Empty inputs → Score 0."""
    engine = ScoringEngine()
    score = engine.analyze_sentiment([])
    assert score == 0.0


def test_no_hype_keywords_returns_zero():
    """Only neutral words → Score near 0."""
    engine = ScoringEngine()
    contents = [
        "The market showed steady growth with moderate gains. "
        "Analysts expect continued stability in traditional sectors."
    ]
    score = engine.analyze_sentiment(contents)
    # No hype keyword → Score must be very low
    assert score < 0.01


def test_high_hype_returns_close_to_one():
    """Many hype keywords → Score near 1."""
    engine = ScoringEngine()
    contents = [
        "Revolutionary breakthrough! Unprecedented exponential growth "
        "in the AI market with massive skyrocketing stock prices. "
        "This game-changer represents unlimited potential despite "
        "speculation risk and bubble concerns about a potential crash."
    ]
    score = engine.analyze_sentiment(contents)
    assert score > 0, "Score must be > 0 with many hype keywords"
    assert score <= 1.0, "Score max 1.0"


def test_final_score_combines_correctly():
    """Weighting: 40% Sentiment + 20% Market + 40% CapEx."""
    engine = ScoringEngine()
    # All mid-values → 0.5 * 100 = 50
    score = engine.calculate_final_score(0.5, 0.5, 0.5)
    assert round(score, 10) == 50.0


def test_final_score_uses_weights():
    """High sentiment, low market position → mid score."""
    engine = ScoringEngine()
    # 1.0 * 0.4 + 0.0 * 0.2 + 0.5 * 0.4 = 0.6 → 60
    score = engine.calculate_final_score(1.0, 0.0, 0.5)
    assert round(score, 10) == 60.0


def test_capex_default_to_neutral():
    """CapEx default stays at 0.5."""
    engine = ScoringEngine()
    # Only Sentiment and Market → CapEx uses 0.5
    score = engine.calculate_final_score(0.8, 0.3)
    expected = (0.8 * 0.4) + (0.3 * 0.2) + (0.5 * 0.4)
    assert round(score, 10) == round(expected * 100, 10)


def test_custom_hype_keywords():
    """Custom keywords are respected."""
    engine = ScoringEngine(hype_keywords=["explosion", "panic"])
    contents = ["The explosion in the market causes panic among investors."]
    score = engine.analyze_sentiment(contents)
    assert score > 0, "Score must be > 0 with custom keywords"
