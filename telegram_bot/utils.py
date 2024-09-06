import os
from telegram import Bot

async def send_telegram_message(chat_id: str, message: str):
    bot_token = os.getenv('ADMIN_BOT_TOKEN')
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message)
