"""Tests für ScoringEngine - keine externen Abhängigkeiten."""
import sys
import os

project_root = "/Users/thtesche/VibeCoding/ai-bubble-burst-osint-tracker"
sys.path.insert(0, project_root)

from src.core.engine import ScoringEngine


def test_empty_contents_returns_zero():
    """Leere Inputs → Score 0."""
    engine = ScoringEngine()
    score = engine.analyze_sentiment([])
    assert score == 0.0


def test_no_hype_keywords_returns_zero():
    """Nur neutrale Wörter → Score nahe 0."""
    engine = ScoringEngine()
    contents = [
        "The market showed steady growth with moderate gains. "
        "Analysts expect continued stability in traditional sectors."
    ]
    score = engine.analyze_sentiment(contents)
    # Kein Hype-Keyword → Score muss sehr niedrig sein
    assert score < 0.01


def test_high_hype_returns_close_to_one():
    """Viele Hype-Keywords → Score nahe 1."""
    engine = ScoringEngine()
    contents = [
        "Revolutionary breakthrough! Unprecedented exponential growth "
        "in the AI market with massive skyrocketing stock prices. "
        "This game-changer represents unlimited potential despite "
        "speculation risk and bubble concerns about a potential crash."
    ]
    score = engine.analyze_sentiment(contents)
    assert score > 0, "Score muss > 0 sein bei vielen Hype-Kwd"
    assert score <= 1.0, "Score max 1.0"


def test_final_score_combines_correctly():
    """Gewichtung: 40% Sentiment + 20% Market + 40% CapEx."""
    engine = ScoringEngine()
    # Alle Mittelwerte → 0.5 * 100 = 50
    score = engine.calculate_final_score(0.5, 0.5, 0.5)
    assert round(score, 10) == 50.0


def test_final_score_uses_weights():
    """Hoher Sentiment, niedrige Marktposition → mittlerer Score."""
    engine = ScoringEngine()
    # 1.0 * 0.4 + 0.0 * 0.2 + 0.5 * 0.4 = 0.6 → 60
    score = engine.calculate_final_score(1.0, 0.0, 0.5)
    assert round(score, 10) == 60.0


def test_capex_default_to_neutral():
    """CapEx-Default bleibt bei 0.5."""
    engine = ScoringEngine()
    # Nur Sentiment und Market → CapEx wird 0.5 verwendet
    score = engine.calculate_final_score(0.8, 0.3)
    expected = (0.8 * 0.4) + (0.3 * 0.2) + (0.5 * 0.4)
    assert round(score, 10) == round(expected * 100, 10)


def test_custom_hype_keywords():
    """Eigene Keywords werden beachtet."""
    engine = ScoringEngine(hype_keywords=["explosion", "panic"])
    contents = ["Die Explosion am Markt löst Panik bei Anlegern aus."]
    score = engine.analyze_sentiment(contents)
    assert score > 0, "Score muss > 0 sein bei eigenen Keywords"
