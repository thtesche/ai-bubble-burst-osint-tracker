import os
import httpx
import asyncio

class FirecrawlEngine:
    """
    Orchestrates discovery and extraction by communicating DIRECTLY with the 
    local Firecrawl (Atlantis) API, bypassing Hermes tool limitations.
    """
    def __init__(self, query: str):
        self.query = query
        # Load base URL from environment variable
        self.base_url = os.getenv("FIRECRAWL_BASE_URL", "http://atlantis:3002/v1").rstrip('/')
        print(f"[*] Firecrawl Engine initialized. Target API: {self.base_url}")

    async def _call_api(self, endpoint: str, payload: dict):
        """Helper to perform async POST requests to the Firecrawl API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"[!] HTTP Error during {endpoint}: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"[!] Unexpected error during {endpoint}: {e}")
        return None

    async def search_and_scrape(self, limit: int = 5, time_filter: str = None):
        """
        Performs a single search call that returns both URLs and their markdown content.
        """
        print(f"[*] Executing direct Search & Scrape for: '{self.query}' (limit={limit})")
        
        payload = {
            "query": self.query,
            "limit": limit,
            "scrapeOptions": {
                "formats": ["markdown"]
            }
        }

        if time_filter:
            payload["tbs"] = time_filter

        data = await self._call_api("search", payload)
        
        if not data or "data" not in data:
            print("[!] No data returned from Firecrawl search.")
            return []

        processed_results = []
        for item in data["data"]:
            content = item.get("content") or item.get("markdown")
            if content:
                processed_results.append({
                    "url": item.get("url"),
                    "title": item.get("title", "No Title"),
                    "markdown": content,  # Ensure 'markdown' key is present for NewsFetcher
                    "content": content    # Keep 'content' for backward compatibility
                })
            else:
                print(f"[!] Item found but no markdown content extracted for: {item.get('url')}")

        print(f"[+] Successfully retrieved {len(processed_results)} articles with content.")
        return processed_results

    async def run_pipeline(self, limit: int = 5):
        """Async pipeline method."""
        return await self.search_and_scrape(limit=limit)