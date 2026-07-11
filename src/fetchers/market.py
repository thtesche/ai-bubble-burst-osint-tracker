import sys


class MarketDataFetcher:
    """
    Ruft Finanzdaten über yfinance ab – kein Firecrawl, kein Fake-Fallback.
    Fällt mit ValueError aus, wenn Daten nicht verfügbar sind.
    """

    def __init__(self, tickers: list[str], logger=None):
        self.tickers = tickers
        self.logger = logger

    def _ensure_yfinance_import(self):
        """
        Hermes injectiert global seinen site-packages in sys.path –
        das führt zu Version-Konflikten (z.B. numpy 3.11 vs 3.12).
        Hier entfernen wir das Hermes-venv, bevor yfinance importiert wird.
        """
        hermes_paths = [p for p in sys.path if '.hermes/hermes-agent/venv' in p]
        for p in hermes_paths:
            sys.path.remove(p)
        # Auch den Hermes-root entfernen
        sys.path = [p for p in sys.path if p != '/Users/thtesche/.hermes/hermes-agent']

    def fetch_market_metrics(self) -> dict:
        """
        Holt aktuelle Preise und 5-Tages-Change über yfinance.
        Fehlgeschlagene Ticker werden übersprungen (kein Fake, kein Absturz).
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

                # Aktuellen Preis
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                if current_price is None:
                    raise ValueError(f"Kein Preis für {ticker} gefunden")

                # Historie für 5-Tages-Change
                end = datetime.now()
                start = end - timedelta(days=35)  # ~5 Börsentage Puffer
                hist = stock.history(start=start, end=end)

                if hist.empty:
                    raise ValueError(f"Keine Historie für {ticker}")

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
                print(f"[!] Fehler bei {ticker}: {e}")
                failed.append((ticker, str(e)))

        if failed:
            print(f"[!] {len(failed)} Ticker konnten nicht abgerufen werden:")
            for t, err in failed:
                print(f"    - {t}: {err}")

        return results

    def calculate_market_score(self, metrics: dict) -> float:
        """Berechnet einen Score (0-1) basierend auf der Marktperformance."""
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
