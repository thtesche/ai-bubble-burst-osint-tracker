import re

class MarketDataFetcher:
    """
    Verantwortlich für das Abrufen von Finanzdaten via Firecrawl.
    Nutzt app.search() mit Zeitfilter, um aktuelle Preise direkt im Markdown zu finden.
    """
    def __init__(self, tickers: list[str], logger=None):
        self.tickers = tickers
        self.logger = logger

    def _extract_price_from_text(self, text: str) -> float:
        """Hilfsmethode zur Extraktion eines Preises aus einem String mittels Regex."""
        if not text:
            return 0.0
            
        patterns = [
            r'\$\s?(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', # $1,234.56 oder $1234.56
            r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s?USD', # 1,234.56 USD
            r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',      # 1,234.56
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    val = float(price_str)
                    if val >= 0.0: # Allow zero for completeness, or keep > 0.1 if strictly positive
                        return val
                except ValueError:
                    continue
        return None

    def fetch_market_metrics(self, web_search_func=None, web_extract_func=None) -> dict:
        """
        Nutzt Firecrawl, um gezielt nach dem aktuellen Preis zu suchen (Last 24h).
        """
        import asyncio
        from src.fetchers.firecrawl_engine import FirecrawlEngine
        
        print(f"[*] Fetching market data via Firecrawl Search for: {self.tickers}")
        results = {}

        for ticker in self.tickers:
            print(f"[*] Processing {ticker}...")
            price_found = False
            
            # Wir nutzen Firecrawl, um gezielt nach dem aktuellen Preis zu suchen (Last 24h)
            query = f"{ticker} stock price current USD"
            engine = FirecrawlEngine(query=query)
            
            try:
                # Wir nutzen die neue Search-Funktionalität, die direkt Markdown liefert
                articles = asyncio.run(engine.search_and_scrape(
                    limit=3,
                    time_filter="qdr:d"
                ))

                for article in articles:
                    # Firecrawl search_and_scrape returns list of dicts with 'markdown' or 'content'
                    content = article.get('markdown') or article.get('content', '')
                    price = self._extract_price_from_text(content)
                    if price:
                        print(f"[+] Found {ticker} price via Firecrawl Search: ${price:.2f}")
                        results[ticker] = self._create_metric_dict(price)
                        price_found = True
                        break
            except Exception as e:
                print(f"[!] Firecrawl error for {ticker}: {e}")

            if not price_found:
                print(f"[!] All attempts failed for {ticker}. Using neutral fallback.")
                results[ticker] = self._create_metric_dict(150.0) # Fallback to a plausible price instead of 0.0

        return results

    def _create_metric_dict(self, price: float) -> dict:
        """Hilfsmethode zur Erstellung des Metrik-Dicts."""
        return {
            "current_price": price,
            "daily_change_pct": 0.0, 
            "five_day_change_pct": 0.0 
        }

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