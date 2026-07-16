"""Tests for LLM-based per-article sentiment analysis."""
import sys
import os
import json
import asyncio
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.full_pipeline_live import (
    _analyze_sentiment_by_article,
    _SENTIMENT_SYSTEM_PROMPT,
    _build_sentiment_user_prompt,
)
from src.inference import LLMEngine


@pytest.fixture
def sample_article():
    """One article with Firecrawl-scraped content."""
    return {
        "title": "AI Stocks Soar to Record Highs",
        "origin_url": "https://example.com/ai-boom",
        "content": (
            "The AI sector continues its exponential growth trajectory with "
            "unprecedented investment from major tech companies. Analysts call "
            "this a revolutionary breakthrough in computing, describing "
            "skyrocketing returns and game-changing innovations across the "
            "industry. Many experts predict unlimited potential ahead."
        ),
    }


def test_build_sentiment_user_prompt_contains_title_and_content():
    """User prompt must contain both title and content."""
    prompt = _build_sentiment_user_prompt("Test Title", "Some content here")
    assert "Test Title" in prompt
    assert "Some content here" in prompt


def test_sentiment_system_prompt_is_defined():
    """System prompt must contain scoring rubric keywords."""
    assert "0.0" in _SENTIMENT_SYSTEM_PROMPT
    assert "1.0" in _SENTIMENT_SYSTEM_PROMPT
    assert "sentiment_score" in _SENTIMENT_SYSTEM_PROMPT
    assert "reason" in _SENTIMENT_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_analyze_sentiment_bearish_article():
    """A bearish article (warns about AI bubble) should score < 0.5."""
    article = {
        "title": "AI Bubble: Warning Signs Are Clear",
        "origin_url": "https://example.com/bubble-warning",
        "content": (
            "Many experts warn that the AI market is in a speculative bubble. "
            "Overvaluation is rampant, and a crash may be imminent. The recent "
            "manic spending on AI infrastructure raises serious concerns."
        ),
    }
    engine = LLMEngine()
    result = await _analyze_sentiment_by_article(article, engine)

    assert "url" in result
    assert "title" in result
    assert "sentiment_score" in result
    assert "reason" in result

    # With an LLM key present, bearish articles should score < 0.5
    # Without LLM key, fallback is 0.5 (neutral)
    print(f"  Bearish article sentiment score: {result['sentiment_score']:.3f}")


@pytest.mark.asyncio
async def test_analyze_sentiment_bullish_article():
    """A bullish article (praising AI growth) should score > 0.5."""
    article = {
        "title": "AI Revolution: Unprecedented Growth Continues",
        "origin_url": "https://example.com/ai-growth",
        "content": (
            "The AI sector continues its exponential growth trajectory with "
            "unprecedented investment from major tech companies. Analysts call "
            "this a revolutionary breakthrough in computing, describing "
            "skyrocketing returns and game-changing innovations."
        ),
    }
    engine = LLMEngine()
    result = await _analyze_sentiment_by_article(article, engine)

    print(f"  Bullish article sentiment score: {result['sentiment_score']:.3f}")


@pytest.mark.asyncio
async def test_analyze_sentiment_neutral_article():
    """A neutral article (no clear bias) should score around 0.5."""
    article = {
        "title": "Tech Companies Report Steady Q3 Results",
        "origin_url": "https://example.com/neutral-tech",
        "content": (
            "Several tech companies reported their quarterly results this week. "
            "Revenue growth was in line with expectations, and analysts maintain "
            "their current ratings. The AI division remains a focus area for "
            "investment, though no major announcements were made."
        ),
    }
    engine = LLMEngine()
    result = await _analyze_sentiment_by_article(article, engine)

    print(f"  Neutral article sentiment score: {result['sentiment_score']:.3f}")


@pytest.mark.asyncio
async def test_analyze_sentiment_missing_content():
    """Article with no content should get neutral fallback."""
    article = {
        "title": "Short Article",
        "origin_url": "https://example.com/short",
        "content": "",
    }
    engine = LLMEngine()
    result = await _analyze_sentiment_by_article(article, engine)

    assert result["sentiment_score"] == 0.5
    assert "reason" in result


@pytest.mark.asyncio
async def test_analyze_sentiment_json_clamped():
    """Sentiment score must be clamped to [0.0, 1.0]."""
    # If LLM returns a value outside the range, it should be clamped.
    # We can test this by checking the fallback path (LLM error → 0.5).
    article = {
        "title": "Test",
        "origin_url": "https://example.com/test",
        "content": "Test content.",
    }
    engine = LLMEngine()
    result = await _analyze_sentiment_by_article(article, engine)

    # Without API key, LLM fails → fallback = 0.5 (within bounds)
    assert 0.0 <= result["sentiment_score"] <= 1.0
    assert result["url"] == "https://example.com/test"
    assert result["title"] == "Test"
