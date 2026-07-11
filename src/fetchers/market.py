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

    def fetch_capex_data(self) -> dict:
        """
        Holt Capital Expenditure (CapEx) aus der Cash Flow Statement über yfinance.
        CapEx wird als negativer Wert (Geldabfluss) ausgewiesen.
        Gibt sowohl jährliche als auch quartalsweise Daten zurück.
        Fehlgeschlagene Ticker werden übersprungen (kein Fake, kein Absturz).
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

                # Jährliche und quartalsweise Cash Flow Statements
                annual_cashflow = stock.cashflow
                quarterly_cashflow = stock.quarterly_cashflow

                capex_data = {}

                # Jährlicher CapEx
                try:
                    annual_capex = annual_cashflow.loc["Capital Expenditure"]
                    capex_data["annual_capex"] = {
                        str(year): float(val)
                        for year, val in annual_capex.dropna().items()
                    }
                except KeyError:
                    # Alternative Keys prüfen
                    capex_data["annual_capex"] = self._extract_capex_from_index(annual_cashflow)

                # Quartalsweiser CapEx (wichtiger für Trendwechsel-Erkennung)
                try:
                    quarterly_capex = quarterly_cashflow.loc["Capital Expenditure"]
                    capex_data["quarterly_capex"] = {
                        str(q): float(val)
                        for q, val in quarterly_capex.dropna().items()
                    }
                except KeyError:
                    capex_data["quarterly_capex"] = self._extract_capex_from_index(quarterly_cashflow)

                # Free Cash Flow optional mitnehmen
                try:
                    annual_fcf = annual_cashflow.loc["Free Cash Flow"]
                    capex_data["annual_free_cash_flow"] = {
                        str(year): float(val)
                        for year, val in annual_fcf.dropna().items()
                    }
                except KeyError:
                    pass  # Optional, nicht kritisch

                print(f"[+] {ticker}: CapEx erfolgreich abgerufen")
                results[ticker] = capex_data

            except Exception as e:
                print(f"[!] Fehler bei CapEx für {ticker}: {e}")
                failed.append((ticker, str(e)))

        if failed:
            print(f"[!] {len(failed)} Ticker konnten nicht abgerufen werden:")
            for t, err in failed:
                print(f"    - {t}: {err}")

        return results

    def _extract_capex_from_index(self, cashflow_df) -> dict:
        """
        Fällt zurück, wenn 'Capital Expenditure' nicht als Index-Key existiert.
        Durchsucht den Index nach ähnlichen Keys und extrahiert die Daten.
        """
        available_indices = cashflow_df.index.tolist()

        # Suche nach alternativen Keys
        capex_keys = [
            k for k in available_indices
            if any(term in str(k).upper() for term in ["CAPITAL EXPENDITURE", "CAPEX", "PPE PURCHASE"])
        ]

        if capex_keys:
            key = capex_keys[0]
            print(f"    [!] '{key}' als CapEx-Alternative verwendet für {self.tickers}")
            series = cashflow_df.loc[key]
            return {str(date): float(val) for date, val in series.dropna().items()}

        # Debug: Zeige verfügbare Indices, wenn nichts passt
        print(f"    [!] 'Capital Expenditure' nicht gefunden für {self.tickers}.")
        print(f"    Verfügbare CashFlow-Indices: {[str(i) for i in available_indices[:20]]}")
        return {}

    def calculate_capex_score(self, capex_data: dict) -> float:
        """
        Berechnet einen Score (0-1) basierend auf der CapEx-Entwicklung.
        0 = niedriges Blasengefahr (CapEx sinkt/stabil), 1 = hohe Gefahr (steigend).
        """
        if not capex_data:
            return 0.5  # Neutral, wenn keine Daten

        # Sammle quartalsweise CapEx für alle Ticker
        # CapEx ist negativ (Geldabfluss) — betrachte Absolutwert
        all_quarterly = {}  # ticker -> {quarter: abs_capex}

        for ticker, data in capex_data.items():
            quarterly = data.get("quarterly_capex", {})
            if quarterly:
                # Negativwerte umkehren (Absolutbetrag der Ausgaben)
                abs_quarterly = {
                    k: abs(float(v)) for k, v in quarterly.items()
                }
                all_quarterly[ticker] = abs_quarterly

        if not all_quarterly:
            return 0.5  # Keine quartalsweisen Daten → neutral

        # Für jeden Ticker: vergleiche neuestes Quartal mit vorherigen
        # Steigende CapEx = höheres Blasengefahr
        ticker_scores = []

        for ticker, quarters in all_quarterly.items():
            if len(quarters) < 2:
                ticker_scores.append(0.5)
                continue

            sorted_quarters = sorted(quarters.keys())
            latest_vals = [float(quarters[q]) for q in sorted_quarters[-4:]]  # Letzte 4 Quartale

            if len(latest_vals) < 2:
                ticker_scores.append(0.5)
                continue

            # Trend berechnen: durchschnittliche Veränderung zwischen aufeinanderfolgenden Quartalen
            changes = []
            for i in range(1, len(latest_vals)):
                if latest_vals[i - 1] != 0:
                    change = (latest_vals[i] - latest_vals[i - 1]) / abs(latest_vals[i - 1])
                    changes.append(change)

            if not changes:
                ticker_scores.append(0.5)
                continue

            avg_change = sum(changes) / len(changes)

            # Mapping: +10% Quartalswachstum → Score 1.0, -10% → Score 0.0
            # Negative CapEx-Veränderung = weniger Investitionen = geringere Blasengefahr
            score = 0.5 + (avg_change / 0.20)  # 20% Wachstum = Score 1.5, clamped
            score = max(0.0, min(1.0, score))
            ticker_scores.append(score)

        return sum(ticker_scores) / len(ticker_scores) if ticker_scores else 0.5

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
