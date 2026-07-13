"""
Interface für Fetcher-Implementierungen

Ein Fetcher ist ein Objekt, das Daten liefert, die die Pipeline
verarbeitet. Die Pipeline erwartet keine spezifischen Klassen,
sondern duck-typisierte Schnittstellen.

## GoogleNewsFetcher

Erwartete Methoden:

```python
class GoogleNewsFetcher:
    def __init__(self, query: str, limit: int = 10, use_firecrawl: bool = True)
    
    def fetch_articles(self) -> dict:
        """
        Gibt ein dict zurück mit:
        {
            "articles": [
                {"title": str, "link": str, "description": str, "content": str},
                ...
            ],
            "total_results": int
        }
        """
    
    def fetch_articles_sync(self) -> dict:
        """Sync-Wrapper für fetch_articles()."""
```

## MarketDataFetcher

Erwartete Methoden:

```python
class MarketDataFetcher:
    def __init__(self, tickers: list[str])
    
    def fetch_market_metrics(self) -> dict:
        """
        Gibt ein dict zurück mit:
        {
            "AAPL": {
                "current_price": float,
                "daily_change_pct": float,
                "five_day_change_pct": float
            },
            ...
        }
        Kann leeres dict zurückgeben (kein error, kein fake!)
        """
    
    def fetch_capex_data(self) -> dict:
        """
        Gibt ein dict zurück mit quarterly/annual CapEx-Daten pro Ticker.
        Kann leeres dict zurückgeben (kein error, kein fake!)
        """
    
    def calculate_capex_score(self, capex_data: dict) -> float:
        """Berechnet einen Score von 0.0 bis 1.0. Gibt 0.5 bei leeren Daten."""
    
    def calculate_market_score(self, metrics: dict) -> float:
        """Berechnet einen Score von 0.0 bis 1.0. Gibt 0.5 bei leeren Daten."""
```

## Mocking für Tests

Zum Testen der Pipeline ohne echte API-Calls kannst du eigene Fetcher
implementieren, die die gleiche Schnittstelle erfüllen:

```python
class MockGoogleNewsFetcher:
    def __init__(self, query, limit=5):
        self.query = query
        self.limit = limit
    
    def fetch_articles(self):
        return {"articles": [], "total_results": 0}

class MockMarketDataFetcher:
    def __init__(self, tickers):
        self.tickers = tickers
    
    def fetch_market_metrics(self):
        return {"AAPL": {"current_price": 150.0, "daily_change_pct": 1.0, "five_day_change_pct": 2.0}}
    
    def fetch_capex_data(self):
        return {"AAPL": {"quarterly_capex": {"2024-01-01": 1000.0}}}
    
    def calculate_capex_score(self, data):
        return 0.5
    
    def calculate_market_score(self, metrics):
        return 0.5
```

Dann übergibst du sie zur Pipeline:

```python
await run_pipeline(
    query="test",
    googlenews_fetcher=MockGoogleNewsFetcher("test"),
    market_fetcher=MockMarketDataFetcher(["AAPL"])
)
```
"""
