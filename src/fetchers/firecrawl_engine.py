import os
import httpx
import asyncio
from typing import Optional


class FirecrawlEngine:
    """
    Minimal Firecrawl engine using the /scrape endpoint.
    Uses cache (maxAge 12h) by default for speed and reliability.
    """
    MAX_AGE_MS = 43_200_000  # 12 hours

    def __init__(self, api_key: str | None = None):
        self.base_url = os.getenv(
            "FIRECRAWL_BASE_URL", "http://atlantis:3002/v1"
        ).rstrip("/")
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")
        if not self.api_key:
            print("[*] Firecrawl Engine: No API key found (local cache mode).")
        else:
            print(f"[*] Firecrawl Engine initialized. Target: {self.base_url}")

    async def scrape(self, url: str) -> Optional[dict]:
        """
        Scrapes a single URL, using cache up to 12 hours old (maxAge).
        Returns {'url': str, 'markdown': str} or None on failure.
        """
        payload = {
            "url": url,
            "formats": ["markdown"],
            "maxAge": self.MAX_AGE_MS,
        }
        if self.api_key:
            payload["apiKey"] = self.api_key

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(f"{self.base_url}/scrape", json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                print(f"[!] Firecrawl scrape failed: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"[!] Unexpected error scraping {url}: {e}")
                return None

        data = response.json()
        # Firecrawl may return {"ok": false, "error": "..."} or
        # {"ok": true, "data": {"errored": true, ...}, "error": "..."}
        if not data or "data" not in data:
            return None

        scraped = data.get("data") or {}
        # 404/errored: page was blocked or doesn't exist
        if scraped.get("errored") or (scraped.get("status") == "failed"):
            err_msg = (scraped.get("error") or
                       data.get("error") or
                       f"blocked/unavailable: {url}")
            print(f"[!] Firecrawl 404/unavailable: {err_msg}")
            return None
        # Explicit ok=false check
        if data.get("ok") is False:
            print(f"[!] Firecrawl returned error for: {url}")
            return None

    def run(self, url: str) -> Optional[dict]:
        """Synchronous wrapper for sync environments.
        
        Must NOT be called from within an async context (e.g., inside asyncio.run(main_async())).
        In async contexts, use: await FirecrawlEngine().scrape(url)
        """
        try:
            # Check if we're already in a running event loop
            try:
                loop = asyncio.get_running_loop()
                raise RuntimeError(
                    "FirecrawlEngine.run() cannot be called from within an async context. "
                    "Use: await FirecrawlEngine().scrape(url)"
                )
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    # No loop running → safe to create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(self.scrape(url))
                    finally:
                        loop.close()
                else:
                    raise  # Re-raise if it's a different RuntimeError (inside async context)
        except Exception as e:
            print(f"[!] Scrape failed: {e}")
            return None
