"""DEPRECATED — do not use.

This file contains a legacy mock market fetcher with hardcoded placeholder data.
Use `src/fetchers/market.py` (yfinance-based) instead.

This file is kept in the repository for historical reference only.

```python
from hermes_tools import web_extract

class MarketFetcher:
    '''
    Fetches market data using web scraping to avoid broken pandas/yfinance dependencies.
    '''
    def __init__(self, tickers: list):
        self.tickers = tickers

    def get_market_metrics(self):
        print(f"[*] Fetching market data via web scraping for: {self.tickers}")
        results = {}

        # For the MVP/Test, we simulate the data or use a very simple scrape.
        # Since real scraping takes time, we'll provide stable mock data
        # to ensure the Telegram delivery can be tested immediately.
        for ticker in self.tickers:
            # In a real scenario, we would use web_extract on Google Finance here.
            # For this immediate fix, we provide realistic mock data to unblock the user.
            results[ticker] = {
                "current_price": 150.0, # Placeholder
                "pct_change_30d": 2.5,  # Placeholder
                "annualized_volatility": 15.0 # Placeholder
            }
            print(f"[+] {ticker}: (Mock Data) 2.5% (30d), Vol: 15.0%")

        return results
```
"""
