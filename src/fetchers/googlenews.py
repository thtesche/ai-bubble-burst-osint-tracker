import urllib.request
import urllib.parse
import re
import os
import asyncio
from email.utils import parsedate_to_datetime


class GoogleNewsFetcher:
    """
    Scrapes Google News RSS feed in parallel to Firecrawl-NewsFetcher.
    - Language: en
    - Limit: 10 results
    - Time filter: last 24 hours
    - Returns total result count (if available)
    - Scrapes URLs with Firecrawl for full content
    """

    def __init__(self, query: str, limit: int = 10, logger=None, use_firecrawl: bool = True):
        self.query = query
        self.limit = limit
        self.logger = logger
        self.use_firecrawl = use_firecrawl  # Whether Firecrawl should be used for URL scraping
        # Firecrawl Engine for URL scraping
        self.firecrawl = None  # Lazily initialized

    def _build_rss_url(self, query: str, limit: int = 10) -> str:
        """Builds the Google News RSS URL."""
        encoded_query = urllib.parse.quote(query)
        return (
            f"https://news.google.com/rss/search?"
            f"q={encoded_query}"
            f"&hl=en&gl=US&ceid=US:en"
            f"&num={limit}"
        )

    def _fetch_rss(self, url: str) -> str:
        """Fetches the RSS feed from Google News."""
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
        """Parses the RSS feed and extracts articles (max limit)."""
        titles = re.findall(r"<title>([^<]+)</title>", xml_data)
        links = re.findall(r"<link>([^<]+)</link>", xml_data)
        dates = re.findall(r"<pubDate>([^<]+)</pubDate>", xml_data)
        descs = re.findall(r"<description>([^<]+)</description>", xml_data)

        articles = []
        # Skip first entry (Google News Header)
        # Return only the first self.limit articles
        max_idx = min(len(titles), len(links), self.limit + 2)
        for i in range(1, max_idx):
            # Clean URL (XML entities decode)
            raw_link = links[i]
            link = (
                raw_link.replace("&amp;", "&")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
            )

            # Skip Google News Header entry (link is news.google.com)
            if link == "https://news.google.com/":
                continue

            # Filter and parse PubDate (for sorting)
            pub_date = dates[i] if i < len(dates) else "N/A"
            if pub_date == "N/A" or pub_date == "":
                continue
            pub_dt = parsedate_to_datetime(pub_date) if pub_date != "N/A" else None

            article = {
                "title": titles[i],
                "link": link,
                "pub_date": pub_date,
                "description": descs[i] if i < len(descs) else "",
                "_pub_dt": pub_dt,
            }
            articles.append(article)

        # Sort by publish date descending (newest first)
        articles.sort(key=lambda a: a.get("_pub_dt"), reverse=True)
        # Remove internal sort key
        for a in articles:
            a.pop("_pub_dt", None)

        return articles

    def _count_total_results(self, xml_data: str) -> int:
        """
        Attempts to extract the total number of results.
        Google News RSS often shows this in the <totalResults> tag or in the title.
        """
        # Attempt 1: totalResults tag
        total_match = re.search(
            r"<totalResults[^>]*>([^<]+)</totalResults>", xml_data
        )
        if total_match:
            try:
                return int(total_match.group(1))
            except ValueError:
                pass

        # Attempt 2: Hidden in title (sometimes "X results" or similar)
        # e.g. "100 results for AI bubble burst"
        title_match = re.search(
            r"(\d+)\s+result", xml_data, re.IGNORECASE
        )
        if title_match:
            try:
                return int(title_match.group(1))
            except ValueError:
                pass

        # Attempt 3: In <title> of first entry (Google News Header)
        all_titles = re.findall(r"<title>([^<]+)</title>", xml_data)
        if len(all_titles) > 0:
            # Example: "AI bubble burst - Google News"
            # or "100 results for AI bubble burst"
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

    async def fetch_articles(self) -> dict:
        """
        Async fetch: Google News RSS + Firecrawl scrape (cache-mode).

        Returns:
            dict with:
                - articles: list[dict] with title, link, pub_date, description
                - total_results: int (total number of results in the last 24h)
                - raw_urls: list[str] (URLs to scrape with Firecrawl)
        """
        rss_url = self._build_rss_url(self.query, self.limit)

        try:
            xml_data = self._fetch_rss(rss_url)
        except Exception as e:
            print(f"[!] Google News RSS fetch failed: {e}")
            return {"articles": [], "total_results": 0, "raw_urls": []}

        articles = self._parse_rss(xml_data)
        total_results = self._count_total_results(xml_data)

        # Extract URLs for Firecrawl scraping
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

        # Scrape URLs with Firecrawl (cache-mode), if Firecrawl available and use_firecrawl=True
        if raw_urls and self.use_firecrawl:
            try:
                from src.fetchers.firecrawl_engine import FirecrawlEngine
                self.firecrawl = FirecrawlEngine()
            except ImportError:
                print("[!] FirecrawlEngine not available - URL scraping skipped")
                self.firecrawl = None

        if raw_urls and self.firecrawl:
            print(f"[*] Scraping {len(raw_urls)} URLs with Firecrawl...")
            try:
                scraped = []
                for url in raw_urls:
                    scrape_result = await self.firecrawl.scrape(url)
                    if scrape_result:
                        scraped.append(scrape_result)
                for i, article in enumerate(articles):
                    if i < len(scraped):
                        article["content"] = scraped[i].get("markdown", "")
            except Exception as e:
                print(f"[!] Firecrawl scraping failed: {e}")

        return result

    def fetch_articles_sync(self) -> dict:
        """Sync wrapper for fetch_articles()."""
        return asyncio.run(self.fetch_articles())
