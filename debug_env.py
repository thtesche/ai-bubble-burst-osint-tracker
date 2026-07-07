
import os
print("--- DEBUG: Environment Variables ---")
print(f"TELEGRAM_BOT_TOKEN exists: {'TELEGRAM_BOT_TOKEN' in os.environ}")
print(f"TELEGRAM_CHAT_ID exists: {'TELEGRAM_CHAT_ID' in os.environ}")
if 'TELEGRAM_BOT_TOKEN' in os.environ:
    print(f"TOKEN value: {os.environ['TELEGRAM_BOT_TOKEN']}")
if 'TELEGRAM_CHAT_ID' in os.environ:
    print(f"CHAT_ID value: {os.environ['TELEGRAM_CHAT_ID']}")
print("-----------------------------------")
