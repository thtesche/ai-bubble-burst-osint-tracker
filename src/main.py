import os
import sys

# Add src to path so we can import our own modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from hermes_tools import web_search, web_extract
import json

class NewsFetcher:
    def __init__(self, query):
        self.query = query

    def fetch_latest_news(self):
        print(f"[*] Searching for: {self.query}")
        search_results = web_search(query=self.query, limit=5)
        
        urls = []
        if "data" in search_results and "web" in search_results["data"]:
            for item in search_results["data"]["web"]:
                urls.append(item["url"])
        
        print(f"[*] Found {len(urls)} URLs. Extracting content...")
        
        extracted_data = []
        if urls:
            # We use web_extract to get markdown content from the URLs
            contents = web_extract(urls=urls)
            for i, res in enumerate(contents.get("results", [])):
                if "error" not in res:
                    extracted_data.append({
                        "url": urls[i],
                        "content": res["content"][:2000] # Limit for prototype
                    })
                else:
                    print(f"[!] Error extracting {urls[i]}: {res['error']}")
        
        return extracted_data

def main():
    print("=== AI Bubble Tracker Prototype ===")
    
    # 1. Setup Query
    query = "AI market bubble news 2026"
    fetcher = NewsFetcher(query)
    
    # 2. Fetch and Extract
    news_items = fetcher.fetch_latest_news()
    
    print(f"\n[+] Successfully extracted {len(news_items)} news items.")
    
    # 3. Preview first item
    if news_items:
        print("\n--- Preview of first item ---")
        print(f"URL: {news_items[0]['url']}")
        print(f"Content Snippet: {news_items[0]['content'][:300]}...")
    else:
        print("\n[-] No news items extracted.")

if __name__ == "__main__":
    main()
