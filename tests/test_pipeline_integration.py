"""Integrationstests für die Pipeline mit Mock-Fetchern."""
import sys
import os
import asyncio
from typing import Optional
import pytest

project_root = "/Users/thtesche/VibeCoding/ai-bubble-burst-osint-tracker"
sys.path.insert(0, project_root)

from src.core.full_pipeline_live import run_pipeline, PipelineError


class MockGoogleNewsFetcher:
    """Gibt leere News → löst PipelineError aus."""
    
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
    """Gibt gültige News zurück."""
    
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
    """Gibt einfache Market-Daten zurück."""
    
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
    """Pipeline muss einen PipelineError werfen, wenn keine News gefunden werden."""
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
    """Pipeline muss erfolgreich mit Mock-Fetchern durchlaufen."""
    mock_news = SuccessMockGoogleNewsFetcher()
    mock_market = MockMarketDataFetcher()
    
    report = asyncio.run(
        run_pipeline(
            query="test",
            googlenews_fetcher=mock_news,
            market_fetcher=mock_market
        )
    )
    
    assert isinstance(report, str), "Report muss ein String sein"
    assert "AI Bubble Burst Report" in report, "Report muss dieheadline enthalten"
    assert "AI Revolution: Unprecedented Growth" in report, "Report muss den Titel enthalten"
    assert "150.00" in report, "Report muss den Preis enthalten"
    # Report darf keine API-Calls an externe Dienste enthalten


def test_pipeline_creates_log_file():
    """Pipeline muss eine JSON-Logdatei im logs/runs/ Verzeichnis erstellen."""
    log_dir = os.path.join(project_root, "logs", "runs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Alte Logs löschen für sauberen Test
    for f in os.listdir(log_dir):
        if f.startswith("googlenews_raw_"):
            os.remove(os.path.join(log_dir, f))
    
    before_count = len([f for f in os.listdir(log_dir) if f.startswith("googlenews_raw_")])
    
    mock_news = SuccessMockGoogleNewsFetcher()
    mock_market = MockMarketDataFetcher()
    
    # Pipeline ausführen
    asyncio.run(
        run_pipeline(
            query="test",
            googlenews_fetcher=mock_news,
            market_fetcher=mock_market
        )
    )
    
    after_count = len([f for f in os.listdir(log_dir) if f.startswith("googlenews_raw_")])
    assert after_count > before_count, "Pipeline muss eine neue Logdatei erstellen"


def test_default_fetchers_when_none_provided():
    """Wenn keine Fetcher übergeben werden, müssen Default-Fetcher erstellt werden."""
    # Dies führt zu echten API-Calls, daher überspringen wir es in CI,
    # aber lokal ist es ein guter Test.
    # async def test_real_pipeline():
    #     report = await run_pipeline()
    #     assert "Bubble Score" in report
    # asyncio.run(test_real_pipeline())
    # Für Tests überspringen wir den echten Call:
    pytest.skip("Echte API-Calls in Tests übersprungen")
