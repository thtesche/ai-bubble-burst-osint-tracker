class NewsFetcher:
    """
    Verantwortlich für das Finden und Extrahieren von Nachrichten-Inhalten.
    Nutzt Firecrawl app.search() für effiziente, aktuelle News im Markdown-Format.
    """
    def __init__(self, query: str, limit: int = 5, logger=None):
        self.base_query = query
        self.limit = limit
        self.logger = logger
        from src.fetchers.firecrawl_engine import FirecrawlEngine
        self.firecrawl = FirecrawlEngine(query=self.base_query)

    async def fetch_and_extract(self) -> list[str]:
        print(f"[*] Starting Firecrawl News Search (Last 24h) for: {self.base_query}")
        
        try:
            # Wir nutzen die neue Search-Funktionalität, die direkt Markdown liefert
            # WICHTIG: Die Engine nutzt self.query aus dem __init__, daher kein 'query' Argument hier!
            articles = await self.firecrawl.search_and_scrape(
                limit=self.limit,
                time_filter="qdr:d"
            )
            
            extracted_contents = [a['markdown'] for a in articles if a.get('markdown')]
            
            if self.logger:
                for i, content in enumerate(extracted_contents):
                    self.logger.save_content("news", f"firecrawl_{i}", content)
            
            return extracted_contents
        except Exception as e:
            print(f"[!] Firecrawl search failed: {e}")
            return []

    def fetch_and_extract_sync(self) -> list[str]:
        import asyncio
        return asyncio.run(self.fetch_and_extract())