import os
import httpx
from typing import Optional


def split_telegram_message(text: str, max_chars: int = 4000) -> list[str]:
    """
    Teilt einen Text in Telegram-kompatible Teile auf.
    Wir nutzen 4000 statt 4096, um etwas Puffer für HTML/Markdown-Tags zu haben.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    while len(text) > max_chars:
        # Versuche zuerst am Zeilenumbruch zu trennen
        split_pos = text.rfind('\n', 0, max_chars)
        
        # Falls kein Zeilenumbruch da ist, trenne am Leerzeichen
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_chars)
            
        # Falls auch das nicht existiert, erzwinge den Schnitt
        if split_pos == -1:
            split_pos = max_chars

        chunks.append(text[:split_pos].strip())
        text = text[split_pos:].strip()

    if text:
        chunks.append(text)
        
    return chunks


class TelegramDelivery:
    """
    Handles sending reports to a specific Telegram user via the Telegram Bot API.
    """
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async def send_report(self, report_text: str):
        """Sends the markdown-formatted report to Telegram."""
        print(f"[*] Attempting to send report to Telegram (Chat ID: {self.chat_id})...")
        
        payload = {
            "chat_id": self.chat_id,
            "text": report_text,
            "parse_mode": "Markdown"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, json=payload)
                if response.status_code == 200:
                    print("[+] Telegram report sent successfully!")
                    return True
                else:
                    print(f"[!] Telegram API error: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                print(f"[!] Failed to send Telegram message: {e}")
                return False

    async def send_structured_report(
        self,
        llm_content: str = "",
        market_metrics: dict | None = None,
        capex_data: dict | None = None,
        googlenews_articles: list[dict] | None = None,
        bubble_score: float = 0.0,
        sentiment_score: float = 0.0,
        market_score: float = 0.0,
        capex_score: float = 0.0,
        model: str = "",
    ) -> bool:
        """
        Sends a structured report to Telegram in priority order:
        1. LLM Risk Evaluation (first message)
        2. Market Data (next message)
        3. Google News (next message)

        Each section is split into chunks if it exceeds 4000 characters.
        """
        if market_metrics is None:
            market_metrics = {}
        if capex_data is None:
            capex_data = {}
        if googlenews_articles is None:
            googlenews_articles = []

        # --- Section 1: LLM Response (highest priority, sent first) ---
        if llm_content.strip():
            print("[*] Sending LLM evaluation to Telegram...")
            header = f"### 🫧 AI Bubble Burst Report\n**Current Bubble Score: {bubble_score:.1f}%**\n"
            if model:
                header += f"**Model**: `{model}`\n\n"

            risk_status = ""
            if bubble_score >= 70:
                risk_status = "**Status:** 🔴 **CRITICAL RISK**\nExtreme signs of overheating and speculative mania.\n\n"
            elif bubble_score >= 40:
                risk_status = "**Status:** 🟡 **MODERATE RISK**\nMixed signals. Significant hype is present, but some fundamental caution remains.\n\n"
            else:
                risk_status = "**Status:** 🟢 **LOW RISK**\nMarket sentiment appears stable or grounded.\n\n"

            llm_text = header + risk_status + f"**📊 Score Breakdown:**\n"
            llm_text += f"- Sentiment Score (News): {sentiment_score:.2f}\n"
            llm_text += f"- Market Score (Prices):  {market_score:.2f}\n"
            llm_text += f"- CapEx Score (Investments): {capex_score:.2f}\n\n"
            llm_text += f"{llm_content}\n"

            chunks = split_telegram_message(llm_text)
            for i, chunk in enumerate(chunks):
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                }

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(self.base_url, json=payload)
                        if response.status_code != 200:
                            print(f"[!] Telegram API error: {response.status_code} - {response.text}")
                            return False
                    except Exception as e:
                        print(f"[!] Failed to send Telegram message: {e}")
                        return False
            print("[+] LLM evaluation sent.")

        # --- Section 2: Market Data ---
        if market_metrics:
            print("[*] Sending market data to Telegram...")
            market_text = "**📈 Market Data:**\n"
            for ticker, data in market_metrics.items():
                market_text += (
                    f"- **{ticker}**: ${data['current_price_dollar']:.2f} "
                    f"(daily: {data['daily_change_percent']:+.2f}%, "
                    f"SMA 200: {data['distance_from_sma_200_percent']:+.2f}%, "
                    f"YTD: {data['ytd_change_percent']:+.2f}%)\n"
                )
            chunks = split_telegram_message(market_text)
            for chunk in chunks:
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                }

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(self.base_url, json=payload)
                        if response.status_code != 200:
                            print(f"[!] Telegram API error: {response.status_code} - {response.text}")
                            return False
                    except Exception as e:
                        print(f"[!] Failed to send Telegram message: {e}")
                        return False
            print("[+] Market data sent.")

        # CapEx section (part of market data)
        if capex_data:
            print("[*] Sending CapEx data to Telegram...")
            capex_text = "**💰 CapEx Summary:**\n"
            for ticker, data in capex_data.items():
                quarterly = data.get("quarterly_capex", {})
                if quarterly:
                    sorted_q = sorted(quarterly.keys(), reverse=True)[:3]
                    latest_vals = [abs(float(quarterly[q])) for q in sorted_q]
                    capex_text += (
                        f"- **{ticker}**: Latest 3 quarters: "
                        f"{', '.join(f'{v:.0f}' for v in latest_vals)}\n"
                    )
            chunks = split_telegram_message(capex_text)
            for chunk in chunks:
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                }

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(self.base_url, json=payload)
                        if response.status_code != 200:
                            print(f"[!] Telegram API error: {response.status_code} - {response.text}")
                            return False
                    except Exception as e:
                        print(f"[!] Failed to send Telegram message: {e}")
                        return False
            print("[+] CapEx data sent.")

        # --- Section 3: Google News ---
        if googlenews_articles:
            print("[*] Sending Google News to Telegram...")
            from email.utils import parsedate_to_datetime

            news_text = "**📰 Google News (neueste 10):**\n"
            for article in googlenews_articles:
                title = article.get("title", "No Title")
                # Prefer originUrl (real source URL); fall back to Google redirect link
                link = article.get("origin_url") or article.get("link", "#")
                raw_date = article.get("pub_date", "")
                try:
                    if raw_date:
                        dt = parsedate_to_datetime(raw_date)
                        date_str = dt.strftime("%d.%m.%Y")
                    else:
                        date_str = "N/A"
                except (ValueError, TypeError):
                    date_str = "N/A"
                news_text += f"- **{date_str}** [{title}]({link})\n"

            chunks = split_telegram_message(news_text)
            for chunk in chunks:
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                }

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(self.base_url, json=payload)
                        if response.status_code != 200:
                            print(f"[!] Telegram API error: {response.status_code} - {response.text}")
                            return False
                    except Exception as e:
                        print(f"[!] Failed to send Telegram message: {e}")
                        return False
            print("[+] Google News sent.")

        print("[+] Structured Telegram delivery complete!")
        return True