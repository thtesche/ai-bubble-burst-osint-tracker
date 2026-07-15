"""Fetcher-Interface für die Pipeline.

Ein Fetcher ist ein duck-typisiertes Objekt, das Daten liefert,
die die Pipeline weiterverarbeitet. Es werden keine spezifischen Klassen erwartet —
nur die beschriebenen Methoden-Signaturen.

## GoogleNewsFetcher

Erwartete Methoden:

```python
class GoogleNewsFetcher:
    def __init__(self, query: str, limit: int = 10, logger=None, use_firecrawl: bool = True)

    async def fetch_articles(self) -> dict:
        '''
        Gibt ein dict zurück mit:
        {
            "articles": [
                {"title": str, "link": str, "origin_url": str | None,
                 "description": str, "pub_date": str, "content": str},
                ...
            ],
            "total_results": int,
            "raw_urls": list[str]  # decoded real URLs for Firecrawl scraping
        }
        '''

    def fetch_articles_sync(self) -> dict:
        '''Sync-Wrapper: asyncio.run(self.fetch_articles()).'''
```

Parameter:
- `query`: Suchabfrage für Google News RSS.
- `limit`: Anzahl der zurückgegebenen Artikel (Standard: 10).
- `logger`: Optionaler RunLogger-Instanz für Logging.
- `use_firecrawl`: Ob URLs mit Firecrawl/Atlantis gescraped werden sollen (Default: True).

## MarketDataFetcher

Erwartete Methoden:

```python
class MarketDataFetcher:
    def __init__(self, tickers: list[str], logger=None)

    def fetch_market_metrics(self) -> dict:
        '''
        Gibt ein dict zurück mit:
        {
            "AAPL": {
                "current_price": float,
                "daily_change_pct": float,
                "five_day_change_pct": float
            },
            ...
        }
        Kann leeres dict zurückgeben (kein error, kein fake!).
        '''

    def fetch_capex_data(self) -> dict:
        '''
        Gibt ein dict zurück mit quarterly/annual CapEx-Daten pro Ticker.
        Kann leeres dict zurückgeben (kein error, kein fake!).
        '''

    def calculate_capex_score(self, capex_data: dict) -> float:
        '''Berechnet einen Score von 0.0 bis 1.0. Gibt 0.5 bei leeren Daten.'''

    def calculate_market_score(self, metrics: dict) -> float:
        '''Berechnet einen Score von 0.0 bis 1.0. Gibt 0.5 bei leeren Daten.'''
```

## Mocking für Tests

Zum Testen der Pipeline ohne echte API-Calls kannst du eigene Fetcher
implementieren, die die gleiche Schnittstelle erfüllen:

```python
class MockGoogleNewsFetcher:
    def __init__(self, query: str = "test", limit: int = 5):
        self.query = query
        self.limit = limit

    async def fetch_articles(self) -> dict:
        return {"articles": [], "total_results": 0, "raw_urls": []}


class SuccessMockGoogleNewsFetcher:
    '''Gibt gültige News zurück — für Tests der Pipeline-Logik.'''
    def __init__(self, query: str = "test", limit: int = 5):
        self.query = query
        self.limit = limit

    async def fetch_articles(self) -> dict:
        return {
            "articles": [
                {
                    "title": "AI Revolution: Unprecedented Growth",
                    "link": "http://test.com/article1",
                    "origin_url": "http://test.com/article1",
                    "description": "This article contains hype keywords like revolution and breakthrough",
                    "content": "This article contains hype keywords like revolution and breakthrough",
                    "pub_date": "Mon, 01 Jan 2025 00:00:00 GMT",
                }
            ],
            "total_results": 1,
            "raw_urls": ["http://test.com/article1"],
        }


class MockMarketDataFetcher:
    def __init__(self, tickers: list[str] | None = None):
        self.tickers = tickers or ["AAPL"]

    def fetch_market_metrics(self) -> dict:
        return {
            "AAPL": {
                "current_price": 150.0,
                "daily_change_pct": 1.0,
                "five_day_change_pct": 2.0,
            }
        }

    def fetch_capex_data(self) -> dict:
        return {
            "AAPL": {
                "quarterly_capex": {"2024-01-01": 1000.0},
            }
        }

    def calculate_capex_score(self, data: dict) -> float:
        return 0.5

    def calculate_market_score(self, metrics: dict) -> float:
        return 0.5
```

Dann übergibst du sie zur Pipeline:

```python
await run_pipeline(
    query="test",
    googlenews_fetcher=SuccessMockGoogleNewsFetcher("test"),
    market_fetcher=MockMarketDataFetcher(["AAPL"])
)
```

## Fehlerbehandlung

- **GoogleNewsFetcher**: Wenn keine Artikel gefunden werden, wirft `run_pipeline()` eine
  `PipelineError`. Es gibt keinen stummen Fallback auf neutrale Werte.
- **MarketDataFetcher**: Leeres dict bei fehlenden Marktdaten wird toleriert — die Pipeline
  fährt mit News-only-Analyse fort. CapEx-Score fällt auf 0.5 (neutral), wenn keine Daten.

"""
