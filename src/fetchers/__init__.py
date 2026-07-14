# Interface for Fetcher Implementations
#
# A Fetcher is an object that provides data for the pipeline
# to process. The pipeline does not expect specific classes,
# but rather duck-typed interfaces.
#
# ## GoogleNewsFetcher
#
# Expected methods:
#
# class GoogleNewsFetcher:
#     def __init__(self, query: str, limit: int = 10, use_firecrawl: bool = True)
#     
#     def fetch_articles(self) -> dict:
#         Returns a dict with:
#         {
#             "articles": [
#                 {"title": str, "link": str, "description": str, "content": str},
#                 ...
#             ],
#             "total_results": int
#         }
#     
#     def fetch_articles_sync(self) -> dict:
#         Sync wrapper for fetch_articles().
#
# ## MarketDataFetcher
#
# Expected methods:
#
# class MarketDataFetcher:
#     def __init__(self, tickers: list[str])
#     
#     def fetch_market_metrics(self) -> dict:
#         Returns a dict with:
#         {
#             "AAPL": {
#                 "current_price": float,
#                 "daily_change_pct": float,
#                 "five_day_change_pct": float
#             },
#             ...
#         }
#         May return empty dict (no error, no fake!)
#     
#     def fetch_capex_data(self) -> dict:
#         Returns a dict with quarterly/annual CapEx data per ticker.
#         May return empty dict (no error, no fake!)
#     
#     def calculate_capex_score(self, capex_data: dict) -> float:
#         Calculates a score from 0.0 to 1.0. Returns 0.5 for empty data.
#     
#     def calculate_market_score(self, metrics: dict) -> float:
#         Calculates a score from 0.0 to 1.0. Returns 0.5 for empty data.
#
# ## Mocking for Tests
#
# To test the pipeline without real API calls, you can implement your own Fetchers
# that fulfill the same interface:
#
# class MockGoogleNewsFetcher:
#     def __init__(self, query, limit=5):
#         self.query = query
#         self.limit = limit
#     
#     def fetch_articles(self):
#         return {"articles": [], "total_results": 0}
#
# class MockMarketDataFetcher:
#     def __init__(self, tickers):
#         self.tickers = tickers
#     
#     def fetch_market_metrics(self):
#         return {"AAPL": {"current_price": 150.0, "daily_change_pct": 1.0, "five_day_change_pct": 2.0}}
#     
#     def fetch_capex_data(self):
#         return {"AAPL": {"quarterly_capex": {"2024-01-01": 1000.0}}}
#     
#     def calculate_capex_score(self, data):
#         return 0.5
#     
#     def calculate_market_score(self, metrics):
#         return 0.5
#
# Then you pass them to the pipeline:
#
# await run_pipeline(
#     query="test",
#     googlenews_fetcher=MockGoogleNewsFetcher("test"),
#     market_fetcher=MockMarketDataFetcher(["AAPL"])
# )
