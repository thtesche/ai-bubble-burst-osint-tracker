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

## MarketDataFetcher

Erwartete Methoden:

```python
class MarketDataFetcher:
    def __init__(self, tickers: list[str], logger=None)

    def fetch_market_metrics(self) -> dict:
        '''Gibt dict mit prices + daily/5d change. Leeres dict bei Fehlern.'''

    def fetch_capex_data(self) -> dict:
        '''Gibt dict mit CapEx data. Leeres dict bei Fehlern.'''

    def calculate_capex_score(self, capex_data: dict) -> float:
        '''Score 0.0–1.0, 0.5 bei leeren Daten.'''

    def calculate_market_score(self, metrics: dict) -> float:
        '''Score 0.0–1.0, 0.5 bei leeren Daten.'''
```

"""
