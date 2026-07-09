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

    async def fetch_and_extract(self) -> list[dict]:
        print(f"[*] Starting Firecrawl News Search (Last 24h) for: {self.base_query}")
        
        try:
            articles = await self.firecrawl.search_and_scrape(
                limit=self.limit,
                time_filter="qdr:d"
            )
            
            processed_articles = []
            for article in articles:
                content = article.get('markdown', '')
                if not content:
                    continue

                processed_articles.append({
                    'title': article.get('title'),
                    'url': article.get('url'),
                    'content': content
                })
            
            return processed_articles
        except Exception as e:
            print(f"[!] Firecrawl search failed: {e}")
            return []

    def fetch_and_extract_sync(self) -> list[dict]:
        import asyncio
        return asyncio.run(self.fetch_and_extract())