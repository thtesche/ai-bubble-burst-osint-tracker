import os
import httpx

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
