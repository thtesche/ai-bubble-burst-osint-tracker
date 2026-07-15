import sys

import pandas as pd


def _extract_scalar(val):
    """
    Extract a scalar float from yfinance cashflow values, which may be:
    - A float/int (normal case)
    - A pandas Series (newer yfinance API with multi-currency metadata)
    - None (missing data)
    Returns float or None.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    # Series case: take the first (and typically only) numeric value
    try:
        if hasattr(val, 'values'):
            # pandas Series - get numeric values
            numeric_vals = [v for v in val.values if isinstance(v, (int, float))]
            if numeric_vals:
                return float(numeric_vals[0])
            # If all values are strings or None, return None
            return None
    except (AttributeError, TypeError):
        pass
    return float(val)


class MarketDataFetcher:
    """
    Fetches financial data via yfinance - no Firecrawl, no fake fallback.
    Raises ValueError when data is unavailable.
    """

    def __init__(self, tickers: list[str], logger=None):
        self.tickers = tickers
        self.logger = logger

    def _ensure_yfinance_import(self):
        """
        Hermes injects its site-packages into sys.path globally -
        this leads to version conflicts (e.g. numpy 3.11 vs 3.12).
        Here we remove the Hermes venv before importing yfinance.
        """
        hermes_paths = [p for p in sys.path if '.hermes/hermes-agent/venv' in p]
        for p in hermes_paths:
            sys.path.remove(p)
        # Also remove the Hermes root
        sys.path = [p for p in sys.path if p != '/Users/thtesche/.hermes/hermes-agent']

    def fetch_market_metrics(self) -> dict:
        """
        Fetches current prices and 5-day change via yfinance.
        Failed tickers are skipped (no fake, no crash).
        """
        self._ensure_yfinance_import()

        import yfinance as yf
        from datetime import datetime, timedelta

        print(f"[*] Fetching market data via yfinance for: {self.tickers}")
        results = {}
        failed = []

        for ticker in self.tickers:
            print(f"[*] Processing {ticker}...")
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Current price
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                if current_price is None:
                    raise ValueError(f"No price found for {ticker}")

                # History for 5-day change
                end = datetime.now()
                start = end - timedelta(days=35)  # ~5 trading days buffer
                hist = stock.history(start=start, end=end)

                if hist.empty:
                    raise ValueError(f"No history found for {ticker}")

                close_series = hist["Close"]
                price_5d_ago = close_series.iloc[0]
                daily_change_pct = ((current_price - close_series.iloc[-1]) / close_series.iloc[-1]) * 100
                five_day_change_pct = ((current_price - price_5d_ago) / price_5d_ago) * 100

                print(f"[+] {ticker}: ${current_price:.2f} (5d: {five_day_change_pct:+.2f}%)")
                results[ticker] = {
                    "current_price": float(round(current_price, 2)),
                    "daily_change_pct": float(round(daily_change_pct, 2)),
                    "five_day_change_pct": float(round(five_day_change_pct, 2)),
                }

            except Exception as e:
                print(f"[!] Error for {ticker}: {e}")
                failed.append((ticker, str(e)))

        if failed:
            print(f"[!] {len(failed)} tickers could not be fetched:")
            for t, err in failed:
                print(f"    - {t}: {err}")

        return results

    def fetch_capex_data(self) -> dict:
        """
        Fetches Capital Expenditure (CapEx) from the Cash Flow Statement via yfinance.
        CapEx is displayed as a negative value (money outflow).
        Returns both annual and quarterly data.
        Failed tickers are skipped (no fake, no crash).
        """
        self._ensure_yfinance_import()

        import yfinance as yf

        print(f"[*] Fetching CapEx data via yfinance for: {self.tickers}")
        results = {}
        failed = []

        for ticker in self.tickers:
            print(f"[*] Processing CapEx for {ticker}...")
            try:
                stock = yf.Ticker(ticker)

                # Annual and quarterly cash flow statements
                annual_cashflow = stock.cashflow
                quarterly_cashflow = stock.quarterly_cashflow

                capex_data = {}

                # Annual CapEx
                try:
                    annual_capex = annual_cashflow.loc["Capital Expenditure"]
                    capex_data["annual_capex"] = {
                        str(year): _extract_scalar(val)
                        for year, val in annual_capex.dropna().items()
                    }
                except KeyError:
                    # Check alternative keys
                    capex_data["annual_capex"] = self._extract_capex_from_index(annual_cashflow)

                # Quarterly CapEx (important for trend change detection)
                try:
                    quarterly_capex = quarterly_cashflow.loc["Capital Expenditure"]
                    capex_data["quarterly_capex"] = {
                        str(q): _extract_scalar(val)
                        for q, val in quarterly_cashflow.dropna().items()
                    }
                except KeyError:
                    capex_data["quarterly_capex"] = self._extract_capex_from_index(quarterly_cashflow)

                # Free Cash Flow optionally included
                try:
                    annual_fcf = annual_cashflow.loc["Free Cash Flow"]
                    capex_data["annual_free_cash_flow"] = {
                        str(year): _extract_scalar(val)
                        for year, val in annual_fcf.dropna().items()
                    }
                except KeyError:
                    pass  # Optional, not critical

                print(f"[+] {ticker}: CapEx fetched successfully")
                results[ticker] = capex_data

            except Exception as e:
                print(f"[!] Error for CapEx for {ticker}: {e}")
                failed.append((ticker, str(e)))

        if failed:
            print(f"[!] {len(failed)} tickers could not be fetched:")
            for t, err in failed:
                print(f"    - {t}: {err}")

        return results

    def _extract_capex_from_index(self, cashflow_df) -> dict:
        """
        Falls back if 'Capital Expenditure' doesn't exist as index key.
        Searches the index for similar keys and extracts the data.
        """
        available_indices = cashflow_df.index.tolist()

        # Search for alternative keys
        capex_keys = [
            k for k in available_indices
            if any(term in str(k).upper() for term in ["CAPITAL EXPENDITURE", "CAPEX", "PPE PURCHASE"])
        ]

        if capex_keys:
            key = capex_keys[0]
            print(f"    [!] Using '{key}' as CapEx alternative for {self.tickers}")
            series = cashflow_df.loc[key]
            return {str(date): _extract_scalar(val) for date, val in series.dropna().items()}

        # Debug: Show available indices if nothing matches
        print(f"    [!] 'Capital Expenditure' not found for {self.tickers}.")
        print(f"    Available CashFlow indices: {[str(i) for i in available_indices[:20]]}")
        return {}

    def calculate_capex_score(self, capex_data: dict) -> float:
        """
        Calculates a score (0-1) based on CapEx development.
        0 = low bubble risk (CapEx decreasing/stable), 1 = high risk (increasing).
        """
        if not capex_data:
            return 0.5  # Neutral if no data

        # Collect quarterly CapEx for all tickers
        # CapEx is negative (money outflow) - use absolute value
        all_quarterly = {}  # ticker -> {quarter: abs_capex}

        for ticker, data in capex_data.items():
            quarterly = data.get("quarterly_capex", {})
            if quarterly:
                # Reverse negative values (absolute value of expenditures)
                # Filter out None values from _extract_scalar before converting
                abs_quarterly = {
                    k: abs(float(v)) for k, v in quarterly.items() if v is not None
                }
                all_quarterly[ticker] = abs_quarterly

        if not all_quarterly:
            return 0.5  # No quarterly data → neutral

        # For each ticker: compare latest quarter with previous quarters
        # Rising CapEx = higher bubble risk
        ticker_scores = []

        for ticker, quarters in all_quarterly.items():
            if len(quarters) < 2:
                ticker_scores.append(0.5)
                continue

            sorted_quarters = sorted(quarters.keys())
            latest_vals = [float(quarters[q]) for q in sorted_quarters[-4:]]  # Last 4 quarters

            if len(latest_vals) < 2:
                ticker_scores.append(0.5)
                continue

            # Calculate trend: average change between consecutive quarters
            changes = []
            for i in range(1, len(latest_vals)):
                if latest_vals[i - 1] != 0:
                    change = (latest_vals[i] - latest_vals[i - 1]) / abs(latest_vals[i - 1])
                    changes.append(change)

            if not changes:
                ticker_scores.append(0.5)
                continue

            avg_change = sum(changes) / len(changes)

            # Mapping: +10% quarterly growth → Score 1.0, -10% → Score 0.0
            # Negative CapEx change = less investment = lower bubble risk
            score = 0.5 + (avg_change / 0.20)  # 20% growth = Score 1.5, clamped
            score = max(0.0, min(1.0, score))
            ticker_scores.append(score)

        return sum(ticker_scores) / len(ticker_scores) if ticker_scores else 0.5

    def calculate_market_score(self, metrics: dict) -> float:
        """Calculates a score (0-1) based on market performance."""
        if not metrics:
            return 0.5

        changes = [m["five_day_change_pct"] for m in metrics.values()]
        avg_change = sum(changes) / len(changes)

        if avg_change <= -5:
            return 1.0
        elif avg_change >= 5:
            return 0.0
        else:
            return 0.5 - (avg_change / 10.0)
