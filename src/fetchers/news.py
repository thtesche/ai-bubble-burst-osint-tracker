from hermes_tools import web_search, web_extract

class NewsFetcher:
    """
    Verantwortlich für das Finden und Extrahieren von Nachrichten-Inhalten.
    Nutzt eine progressive Multi-Intent Suchstrategie für maximale Resilienz.
    """
    def __init__(self, query: str, limit: int = 5, logger=None):
        self.base_query = query
        self.limit = limit
        self.logger = logger

    def fetch_and_extract(self) -> list[str]:
        print(f"[*] Starting Progressive Multi-Intent News Fetching for: {self.base_query}")
        
        # Strategien von sehr breit zu spezifisch, um die Trefferwahrscheinlichkeit zu maximieren
        strategies = [
            {"name": "broad", "query": self.base_query},
            {"name": "ai_hype", "query": f"{self.base_query} hype bubble"},
            {"name": "tech_news", "query": f"{self.base_query} tech news"},
            {"name": "finance_focus", "query": f"site:finance.yahoo.com {self.base_query}"},
            {"name": "fast_fallback", "query": "artificial intelligence market trends"}
        ]

        extracted_contents = []
        found_urls = []
        found_descriptions = []

        for strategy in strategies:
            print(f"[*] Trying Strategy: {strategy['name']} (Query: {strategy['query']})")
            search_results = web_search(query=strategy['query'], limit=self.limit)
            
            if self.logger:
                self.logger.save_search_results(f"news_{strategy['name']}", search_results)

            if "data" in search_results and "web" in search_results["data"]:
                web_items = search_results["data"]["web"]
                if len(web_items) > 0:
                    found_urls = [item["url"] for item in web_items]
                    found_descriptions = [item.get("description", "") for item in web_items]
                    print(f"[+] Strategy {strategy['name']} found {len(found_urls)} URLs.")
                    break 
                else:
                    print(f"[-] Strategy {strategy['name']} yielded no URLs.")
            else:
                print(f"[-] Strategy {strategy['name']} returned no data.")

        if not found_urls:
            print("[-] All search strategies failed to find URLs.")
            return []

        print(f"[*] Attempting extraction on {len(found_urls)} URLs...")
        extraction_results = web_extract(urls=found_urls)
        
        for i, res in enumerate(extraction_results.get("results", [])):
            url = found_urls[i] if i < len(found_urls) else "unknown"
            if "error" not in res and res.get("content"):
                content = res["content"]
                print(f"[+] Successfully extracted: {url}")
                extracted_contents.append(content)
                if self.logger:
                    self.logger.save_content("news", f"article_{i}", content)
            else:
                # Fallback auf Snippet aus der letzten erfolgreichen Suche
                snippet = found_descriptions[i] if i < len(found_descriptions) else ""
                if snippet:
                    print(f"[!] Extraction failed for {url}. Using search snippet fallback.")
                    extracted_contents.append(f"Snippet from search: {snippet}")
                    if self.logger:
                        self.logger.save_content("news", f"fallback_{i}", snippet)
                else:
                    print(f"[!] Extraction failed and no snippet available for {url}")

        return extracted_contents
