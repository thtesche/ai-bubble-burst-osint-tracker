"""Integration tests for the pipeline with mock fetchers."""
import sys
import os
import asyncio
from typing import Optional
import pytest

project_root = "/Users/thtesche/VibeCoding/ai-bubble-burst-osint-tracker"
sys.path.insert(0, project_root)

from src.core.full_pipeline_live import run_pipeline, PipelineError, PipelineResult


class MockGoogleNewsFetcher:
    """Returns empty news → raises PipelineError."""
    
    __annotations__ = {
        "query": str,
        "limit": int
    }
    
    def __init__(self, query: str = "", limit: int = 5):
        self.query = query
        self.limit = limit
    
    def fetch_articles(self) -> dict:
        return {"articles": [], "total_results": 0}


class SuccessMockGoogleNewsFetcher:
    """Returns valid news."""
    
    __annotations__ = {
        "query": str,
        "limit": int
    }
    
    def __init__(self, query: str = "test", limit: int = 5):
        self.query = query
        self.limit = limit
    
    def fetch_articles(self) -> dict:
        return {
            "articles": [
                {
                    "title": "AI Revolution: Unprecedented Growth",
                    "link": "http://test.com/article1",
                    "description": "This article contains hype keywords like revolution and breakthrough",
                    "content": "This article contains hype keywords like revolution and breakthrough"
                }
            ],
            "total_results": 1
        }


class MockMarketDataFetcher:
    """Returns simple market data."""
    
    __annotations__ = {
        "tickers": list[str]
    }
    
    def __init__(self, tickers: Optional[list[str]] = None):
        self.tickers = tickers or ["AAPL"]
    
    def fetch_market_metrics(self) -> dict:
        return {
            "AAPL": {
                "current_price": 150.0,
                "daily_change_pct": 1.0,
                "five_day_change_pct": 2.0
            }
        }
    
    def fetch_capex_data(self) -> dict:
        return {
            "AAPL": {
                "quarterly_capex": {"2024-01-01": 1000.0}
            }
        }
    
    def calculate_capex_score(self, data: dict) -> float:
        return 0.5
    
    def calculate_market_score(self, metrics: dict) -> float:
        return 0.5


def test_pipeline_raises_error_on_empty_news():
    """Pipeline must raise a PipelineError when no news is found."""
    mock_news = MockGoogleNewsFetcher()
    mock_market = MockMarketDataFetcher()
    
    with pytest.raises(PipelineError, match="Failed to fetch Google News articles"):
        asyncio.run(
            run_pipeline(
                query="test",
                googlenews_fetcher=mock_news,
                market_fetcher=mock_market
            )
        )


def test_pipeline_runs_successfully_with_mocks():
    """Pipeline must run successfully with mock fetchers."""
    mock_news = SuccessMockGoogleNewsFetcher()
    mock_market = MockMarketDataFetcher()
    
    report = asyncio.run(
        run_pipeline(
            query="test",
            googlenews_fetcher=mock_news,
            market_fetcher=mock_market
        )
    )
    
    assert isinstance(report, PipelineResult), "Report must be a PipelineResult"
    assert report.bubble_score > 0, "Bubble score must be calculated"
    assert len(report.googlenews_articles) > 0, "Must contain Google News articles"
    assert "AAPL" in report.market_metrics, "Must contain market metrics"
    # LLM may or may not have run (depends on API key), so llm_content can be empty


def test_pipeline_creates_log_file():
    """Pipeline must create a JSON log file in the logs/runs/ directory."""
    log_dir = os.path.join(project_root, "logs", "runs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Delete old logs for clean test
    for f in os.listdir(log_dir):
        if f.startswith("googlenews_raw_"):
            os.remove(os.path.join(log_dir, f))
    
    before_count = len([f for f in os.listdir(log_dir) if f.startswith("googlenews_raw_")])
    
    mock_news = SuccessMockGoogleNewsFetcher()
    mock_market = MockMarketDataFetcher()
    
    # Run pipeline
    asyncio.run(
        run_pipeline(
            query="test",
            googlenews_fetcher=mock_news,
            market_fetcher=mock_market
        )
    )
    
    after_count = len([f for f in os.listdir(log_dir) if f.startswith("googlenews_raw_")])
    assert after_count > before_count, "Pipeline must create a new log file"


def test_default_fetchers_when_none_provided():
    """When no fetchers are provided, default fetchers must be created."""
    # This triggers real API calls, so we skip it in CI,
    # but locally it's a good test.
    # async def test_real_pipeline():
    #     report = await run_pipeline()
    #     assert "Bubble Score" in report
    # asyncio.run(test_real_pipeline())
    # For tests we skip the real call:
    pytest.skip("Real API calls skipped in tests")
