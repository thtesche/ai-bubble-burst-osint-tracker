import re

class MarketDataFetcher:
    """
    Verantwortlich für das Abrufen von Finanzdaten via Search-Snippets & Deep Extraction.
    Nutzt eine Kaskade: Snippet -> Deep Extraction (web_extract) -> Fallback.
    """
    def __init__(self, tickers: list[str]):
        self.tickers = tickers

    def _extract_price_from_text(self, text: str) -> float | None:
        """Hilfsmethode zur Extraktion eines Preises aus einem String mittels Regex."""
        if not text:
            return None
            
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
                    if val > 0.1: # Plausibilitätscheck
                        return val
                except ValueError:
                    continue
        return None

    def fetch_market_metrics(self, web_search_func, web_extract_func) -> dict:
        """
        Nutzt eine Kaskade von Such- und Extraktionsmethoden.
        """
        print(f"[*] Fetching market data via Cascade for: {self.tickers}")
        results = {}

        for ticker in self.tickers:
            print(f"[*] Processing {ticker}...")
            price_found = False
            
            # 1. Suche nach URLs und Snippets
            query = f"{ticker} stock price current"
            search_results = web_search_func(query=query, limit=5)
            
            if "data" in search_results and "web" in search_results["data"]:
                web_items = search_results["data"]["web"]
                
                for item in web_items:
                    url = item.get("url")
                    snippet = item.get("description", "")

                    # Versuch A: Preis direkt aus dem Snippet extrahieren (schnell)
                    price = self._extract_price_from_text(snippet)
                    
                    if price:
                        print(f"[+] Found {ticker} price in snippet: ${price:.2f}")
                        results[ticker] = self._create_metric_dict(price)
                        price_found = True
                        break
                    
                    # Versuch B: Deep Extraction der Seite (falls Snippet fehlschlägt)
                    if url:
                        print(f"[*] Snippet failed for {ticker}. Attempting Deep Extraction on {url}...")
                        extraction = web_extract_func(urls=[url])
                        for res in extraction.get("results", []):
                            if "error" not in res and res.get("content"):
                                price = self._extract_price_from_text(res["content"])
                                if price:
                                    print(f"[+] Found {ticker} price via Deep Extraction: ${price:.2f}")
                                    results[ticker] = self._create_metric_dict(price)
                                    price_found = True
                                    break
                        if price_found:
                            break

            if not price_found:
                print(f"[!] All attempts failed for {ticker}. Using neutral fallback.")
                results[ticker] = self._create_metric_dict(0.0) # Neutraler Wert

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
