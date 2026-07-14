import os
import sys
import asyncio

# Add project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.full_pipeline_live import run_pipeline
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
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_env(env_path)

    # 1. Configuration
    SEARCH_QUERY = os.getenv("SEARCH_QUERY", "AI market bubble burst risk analysis 2025 2026")
    MARKET_TICKERS = [t.strip() for t in os.getenv("MARKET_TICKERS", "MSFT,GOOGL,AMZN,META,NVDA,AMD,ASML,AVGO,MU,DELL,SMCI,HPE").split(",") if t.strip()]
    LIMIT = int(os.getenv("PIPELINE_LIMIT", "5"))

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # LLM Configuration (read from .env, used by LLMEngine)
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # 2. Execute Pipeline: Full E2E (News + Market + CapEx)
    print("[*] Running full pipeline (Firecrawl + Google News + yfinance)...\n")
    report = await run_pipeline(query=SEARCH_QUERY, limit=LIMIT, tickers=MARKET_TICKERS)

    # 3. Output Report to console
    print("\n--- FINAL LIVE REPORT ---")
    print(report)

    # 4. Delivery: Telegram (ACTIVE)
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
