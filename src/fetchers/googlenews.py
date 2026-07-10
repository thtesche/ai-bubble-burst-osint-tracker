import urllib.request
import urllib.parse
import re
import os
import asyncio


class GoogleNewsFetcher:
    """
    Scrapst Google News RSS-Feed parallel zum Firecrawl-NewsFetcher.
    - Sprache: en
    - Limit: 10 Treffer
    - Zeitfilter: letzte 24h
    - Gibt Gesamtreffer-Anzahl zurück (wenn verfügbar)
    - Scrapst URLs mit Firecrawl für vollständige Inhalte
    """

    def __init__(self, query: str, limit: int = 10, logger=None, use_firecrawl: bool = True):
        self.query = query
        self.limit = limit
        self.logger = logger
        self.use_firecrawl = use_firecrawl  # Ob Firecrawl für URL-Scraping verwendet werden soll
        # Firecrawl Engine für URL-Scraping
        self.firecrawl = None  # Wird lazy initialisiert

    def _build_rss_url(self, query: str, limit: int = 10) -> str:
        """Baut die Google News RSS URL."""
        encoded_query = urllib.parse.quote(query)
        return (
            f"https://news.google.com/rss/search?"
            f"q={encoded_query}"
            f"&hl=en&gl=US&ceid=US:en"
            f"&num={limit}"
        )

    def _fetch_rss(self, url: str) -> str:
        """Holt den RSS-Feed von Google News."""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")

    def _parse_rss(self, xml_data: str) -> list[dict]:
        """Parsst den RSS-Feed und extrahiert Artikel (max limit)."""
        titles = re.findall(r"<title>([^<]+)</title>", xml_data)
        links = re.findall(r"<link>([^<]+)</link>", xml_data)
        dates = re.findall(r"<pubDate>([^<]+)</pubDate>", xml_data)
        descs = re.findall(r"<description>([^<]+)</description>", xml_data)

        articles = []
        # Ersten Eintrag (Google News Header) überspringen
        # Nur die ersten self.limit Artikel zurückgeben
        max_idx = min(len(titles), len(links), self.limit + 2)
        for i in range(1, max_idx):
            # URL bereinigen (XML-Entities decode)
            raw_link = links[i]
            link = (
                raw_link.replace("&amp;", "&")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
            )

            # Google News Header-Eintrag überspringen (Link ist news.google.com)
            if link == "https://news.google.com/":
                continue

            # PubDate filtern (nur gültige Daten)
            pub_date = dates[i] if i < len(dates) else "N/A"
            if pub_date == "N/A" or pub_date == "":
                continue

            article = {
                "title": titles[i],
                "link": link,
                "pub_date": pub_date,
                "description": descs[i] if i < len(descs) else "",
            }
            articles.append(article)

        return articles

    def _count_total_results(self, xml_data: str) -> int:
        """
        Versucht, die Gesamtzahl der Treffer zu extrahieren.
        Google News RSS zeigt diese oft im <totalResults>-Tag oder im title.
        """
        # Versuche 1: totalResults Tag
        total_match = re.search(
            r"<totalResults[^>]*>([^<]+)</totalResults>", xml_data
        )
        if total_match:
            try:
                return int(total_match.group(1))
            except ValueError:
                pass

        # Versuche 2: Im title versteckt (manchmal "X results" oder ähnlich)
        # z.B. "100 results for AI bubble burst"
        title_match = re.search(
            r"(\d+)\s+result", xml_data, re.IGNORECASE
        )
        if title_match:
            try:
                return int(title_match.group(1))
            except ValueError:
                pass

        # Versuche 3: Im <title> des ersten Eintrags (Google News Header)
        all_titles = re.findall(r"<title>([^<]+)</title>", xml_data)
        if len(all_titles) > 0:
            # Beispiel: "AI bubble burst - Google News"
            # oder "100 results for AI bubble burst"
            title1 = all_titles[0]
            count_match = re.search(
                r"(\d+)\s+results?", title1, re.IGNORECASE
            )
            if count_match:
                try:
                    return int(count_match.group(1))
                except ValueError:
                    pass

        return 0

    def fetch_articles(self) -> dict:
        """
        Holt Google News Artikel und scrapst URLs mit Firecrawl.

        Returns:
            dict mit:
                - articles: list[dict] mit title, link, pub_date, description
                - total_results: int (Gesamtzahl der Treffer in den letzten 24h)
                - raw_urls: list[str] (URLs zum Scrapen mit Firecrawl)
        """
        rss_url = self._build_rss_url(self.query, self.limit)

        try:
            xml_data = self._fetch_rss(rss_url)
        except Exception as e:
            print(f"[!] Google News RSS fetch failed: {e}")
            return {"articles": [], "total_results": 0, "raw_urls": []}

        articles = self._parse_rss(xml_data)
        total_results = self._count_total_results(xml_data)

        # URLs für Firecrawl Scraping extrahieren
        raw_urls = [a["link"] for a in articles]

        result = {
            "articles": articles,
            "total_results": total_results,
            "raw_urls": raw_urls,
        }

        print(
            f"[+] Google News: Found {len(articles)} articles "
            f"(total 24h results: {total_results})"
        )

        # URLs mit Firecrawl scrapen, wenn Engine verfügbar und use_firecrawl=True
        if raw_urls and self.use_firecrawl and self.firecrawl is None:
            from src.fetchers.firecrawl_engine import FirecrawlEngine
            self.firecrawl = FirecrawlEngine(query=self.query)

        if raw_urls and self.firecrawl:
            print(f"[*] Scraping {len(raw_urls)} URLs with Firecrawl...")
            try:
                scraped = asyncio.run(
                    self.firecrawl.search_and_scrape(
                        limit=self.limit, time_filter="qdr:d"
                    )
                )
                # Scraped content zu Artikeln hinzufügen
                for i, article in enumerate(articles):
                    if i < len(scraped):
                        article["content"] = (
                            scraped[i].get("markdown")
                            or scraped[i].get("content", "")
                        )
            except Exception as e:
                print(f"[!] Firecrawl scraping failed: {e}")

        return result

    def fetch_articles_sync(self) -> dict:
        """Sync wrapper für fetch_articles()."""
        return self.fetch_articles()
