import sys

# Strip Hermes venv paths **before** any third-party imports.
# Without this, the Hermes venv's broken pandas (Python 3.11) is picked up
# during module import — before _ensure_yfinance_import() can run.
_hermes_paths = [p for p in sys.path if '.hermes/hermes-agent/venv' in p or p == '/Users/thtesche/.hermes/hermes-agent']
for _p in _hermes_paths:
    sys.path.remove(_p)
sys.path = [p for p in sys.path if '.hermes' not in p]
del _hermes_paths


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
        Fetches current prices, 200-day SMA distance, and Year-to-Date performance
        via yfinance. 5-day change replaced by macro-stable indicators.
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

                # History for 200-day SMA and YTD (need ~250 trading days)
                end = datetime.now()
                start = end - timedelta(days=280)  # ~250 trading days
                hist = stock.history(start=start, end=end)

                if hist.empty:
                    raise ValueError(f"No history found for {ticker}")

                close_series = hist["Close"]

                # Daily change (last close vs previous close)
                if len(close_series) < 2:
                    daily_percent = 0.0
                else:
                    daily_percent = (
                        (close_series.iloc[-1] - close_series.iloc[-2])
                        / close_series.iloc[-2]
                    ) * 100

                # 200-day Simple Moving Average
                if len(close_series) >= 200:
                    sma_200 = close_series.iloc[-200:].mean()
                    distance_from_sma_200 = (
                        (current_price - sma_200) / sma_200
                    ) * 100
                else:
                    # Not enough data — use shorter window (at least 50 days)
                    lookback = max(len(close_series) - 1, 50)
                    sma_200 = close_series.iloc[-lookback:].mean()
                    distance_from_sma_200 = (
                        (current_price - sma_200) / sma_200
                    ) * 100

                # Year-to-Date performance
                ytd_start = end.replace(month=1, day=1)
                ytd_hist = stock.history(start=ytd_start, end=end)
                if not ytd_hist.empty:
                    ytd_close = ytd_hist["Close"].iloc[0]
                    ytd_percent = ((current_price - ytd_close) / ytd_close) * 100
                else:
                    ytd_percent = 0.0  # No YTD data (new listing)

                print(f"[+] {ticker}: ${current_price:.2f} (SMA 200 dist: {distance_from_sma_200:+.2f}%, YTD: {ytd_percent:+.2f}%)")
                results[ticker] = {
                    "current_price_dollar": float(round(current_price, 2)),
                    "daily_change_percent": float(round(daily_percent, 2)),
                    "distance_from_sma_200_percent": float(round(distance_from_sma_200, 2)),
                    "ytd_change_percent": float(round(ytd_percent, 2)),
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
                        for q, val in quarterly_capex.dropna().items()
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
        
        Strategy (priority order):
        1. Exact match on "Capital Expenditure" (works for some tickers).
        2. Fuzzy match on common yfinance labels:
           "Purchase of Property and Equipment", "Capital Spending",
           "Purchase of Fixed Assets", "Purchase of Plant and Equipment",
           "Capital Expenditure", "CAPEX", "PPE PURCHASE".
        3. Last resort: pick the investing-activity row that best matches
           CapEx semantics (contains "Purchase" + one of "Property/Equipment/
           Fixed Assets/Plant").
        """
        available_indices = cashflow_df.index.tolist()
        upper_indices = {str(k).upper(): str(k) for k in available_indices}

        # Priority 1 & 2: broad exact / substring matching
        priority_terms = [
            # Standardized labels used by yfinance for different tickers
            "CAPITAL EXPENDITURE",
            "CAPEX",
            "PPE PURCHASE",
            "PURCHASE OF PROPERTY AND EQUIPMENT",
            "PURCHASE OF FIXED ASSETS",
            "PURCHASE OF PLANT AND EQUIPMENT",
            "CAPITAL SPENDING",
        ]

        capex_keys = []
        for term in priority_terms:
            matches = [
                upper_indices[u] for u in upper_indices if term in u
            ]
            if matches:
                capex_keys = matches
                break

        if capex_keys:
            key = capex_keys[0]
            print(f"    [!] Using '{key}' as CapEx key for {self.tickers}")
            series = cashflow_df.loc[key]
            return {
                str(date): _extract_scalar(val)
                for date, val in series.dropna().items()
            }

        # Priority 3: heuristic — pick a row that looks like CapEx:
        #   Must contain "PURCHASE" AND (one of: "PROPERTY" / "EQUIPMENT" /
        #   "FIXED" / "PLANT" / "ASSETS" / "PROPERTY AND EQUIPMENT")
        heuristic_terms = [
            "PROPERTY AND EQUIPMENT",
            "PROPERTY",
            "EQUIPMENT",
            "FIXED ASSETS",
            "PLANT",
        ]
        for idx_label in available_indices:
            label = str(idx_label).upper()
            if "PURCHASE" not in label:
                continue
            if any(t in label for t in heuristic_terms):
                print(f"    [!] Heuristic CapEx match: '{idx_label}' for {self.tickers}")
                series = cashflow_df.loc[idx_label]
                return {
                    str(date): _extract_scalar(val)
                    for date, val in series.dropna().items()
                }

        # Give up — log available indices for debugging
        print(
            f"    [!] 'Capital Expenditure' not found for {self.tickers}."
        )
        print(
            f"    Available CashFlow indices: {[str(i) for i in available_indices[:20]]}"
        )
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
        """
        Calculates a macro-market bubble score (0-1) based on long-term indicators.
        0 = stable/low risk, 1 = high bubble risk.

        Uses two long-term indicators:
        1. Distance from 200-day SMA (SMA 200):
           - 0-20% above → 0.0 risk (fairly valued)
           - 20-50% above → 0.0-1.0 (bubble territory, linear scale)
           - 50%+ above → 1.0 (extreme overvaluation)
           - Price below SMA 200 → 0.0 (not in bubble)

        2. Year-to-Date (YTD) performance:
           - 0-30% YTD → 0.0 risk (reasonable growth)
           - 30-70% YTD → 0.0-1.0 (exuberant, linear scale)
           - 70%+ YTD → 1.0 (extreme YTD surge)

        Both indicators are averaged for the final score.
        Returns 0.5 (neutral) if no data available.
        """
        if not metrics:
            return 0.5

        sma_scores = []
        ytd_scores = []

        for ticker, data in metrics.items():
            # — SMA 200 distance score —
            dist_from_sma = data.get("distance_from_sma_200_percent", 0.0)
            if dist_from_sma <= 20:
                sma_scores.append(0.0)
            elif dist_from_sma >= 50:
                sma_scores.append(1.0)
            else:
                sma_scores.append((dist_from_sma - 20.0) / 30.0)

            # — YTD performance score —
            ytd = data.get("ytd_change_percent", 0.0)
            if ytd <= 30:
                ytd_scores.append(0.0)
            elif ytd >= 70:
                ytd_scores.append(1.0)
            else:
                ytd_scores.append((ytd - 30.0) / 40.0)

        avg_sma = sum(sma_scores) / len(sma_scores) if sma_scores else 0.0
        avg_ytd = sum(ytd_scores) / len(ytd_scores) if ytd_scores else 0.0

        return (avg_sma + avg_ytd) / 2.0
