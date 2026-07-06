from hermes_tools import web_search, web_extract

class NewsFetcher:
    """
    Verantwortlich für das Finden und Extrahieren von Nachrichten-Inhalten.
    Nutzt gezielt Yahoo Finance als primäre Quelle, um Bot-Schutz zu umgehen.
    """
    def __init__(self, query: str, limit: int = 5):
        # Wir ergänzen die Query automatisch um den Yahoo Finance Fokus
        self.query = f"site:finance.yahoo.com {query}"
        self.limit = limit

    def fetch_and_extract(self) -> list[str]:
        """
        Sucht nach News und extrahiert den Textinhalt der gefundenen URLs.
        Nutzt Fallbacks auf Such-Snippets, falls die Extraktion fehlschlägt.
        """
        print(f"[*] Searching Yahoo Finance for: {self.query}")
        search_results = web_search(query=self.query, limit=self.limit)
        
        extracted_contents = []
        
        if "data" in search_results and "web" in search_results["data"]:
            web_items = search_results["data"]["web"]
            urls = [item["url"] for item in web_items]
            descriptions = [item.get("description", "") for item in web_items]

            if not urls:
                print("[-] No URLs found.")
                return []

            print(f"[*] Found {len(urls)} potential URLs. Attempting extraction...")
            
            # Versuch der Extraktion via web_extract
            extraction_results = web_extract(urls=urls)
            
            for i, res in enumerate(extraction_results.get("results", [])):
                url = urls[i]
                if "error" not in res and res.get("content"):
                    # Erfolg: Wir haben den vollen Text
                    content = res["content"]
                    print(f"[+] Successfully extracted: {url}")
                    extracted_contents.append(content)
                else:
                    # Fallback: Wir nutzen das Snippet aus der Suche
                    snippet = descriptions[i] if i < len(descriptions) else ""
                    if snippet:
                        print(f"[!] Extraction failed for {url}. Using search snippet fallback.")
                        extracted_contents.append(f"Snippet from search: {snippet}")
                    else:
                        print(f"[!] Extraction failed and no snippet available for {url}")

        return extracted_contents
