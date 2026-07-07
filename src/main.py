import os
import sys
import asyncio

# Add project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fetchers.firecrawl_engine import FirecrawlEngine
from src.fetchers.market_fetcher import MarketFetcher
from src.core.analyzer import BubbleAnalyzer
from src.delivery.telegram import TelegramDelivery

def load_env(filepath):
    """Manually loads environment variables from a .env file."""
    if os.path.exists(filepath):
        print(f"[*] Loading environment from {filepath}")
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print(f"[!] Warning: .env file not found at {filepath}")

async def main_async():
    print("==========================================")
    print("   🚀 AI BUBBLE BURST OSINT TRACKER       ")
    print("==========================================\n")

    # Load .env at the very beginning
    load_env(os.path.join(os.path.dirname(__file__), '..', '.env'))

    # 1. Configuration
    SEARCH_QUERY = "AI market bubble burst risk analysis 2025 2026"
    MARKET_TICKERS = ["NVDA", "MSFT", "AAPL", "^IXIC"]
    LIMIT = 5

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # 2. Initialize Components
    engine = FirecrawlEngine(query=SEARCH_QUERY)
    analyzer = BubbleAnalyzer()

    # 3. Execute Pipeline: Data Collection
    print("[*] Phase 1: Collecting News via Firecrawl...")
    articles = await engine.run_pipeline(limit=LIMIT)

    # --- DEACTIVATED: Market Data due to yfinance/pandas dependency issue ---
    print("[!] Phase 2: Skipping Market Data (yfinance/pandas dependency issue)")
    market_data = None 
    # -----------------------------------------------------------------------

    if not articles and not market_data:
        print("[!] No data collected. Exiting.")
        return

    # 4. Execute Pipeline: Analysis (Qualitative only for now)
    print("[*] Phase 3: Analyzing collected data...")
    score, findings, market_summary = analyzer.analyze_content(articles, market_data)

    # 5. Generate Report
    report = analyzer.generate_report(score, findings, market_summary)

    # 6. Output Result
    print("\n--- FINAL LIVE REPORT ---")
    print(report)

    # 7. Delivery: Telegram (ACTIVE)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n[*] Phase 4: Delivering report via Telegram...")
        delivery = TelegramDelivery(bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)
        success = await delivery.send_report(report)
        if success:
            print("[+] Delivery successful!")
        else:
            print("[!] Delivery failed.")
    else:
        print(f"\n[!] Telegram credentials missing in .env. (Token: {bool(TELEGRAM_BOT_TOKEN)}, ChatID: {bool(TELEGRAM_CHAT_ID)})")

    print("\n==========================================")

if __name__ == '__main__':
    asyncio.run(main_async())
