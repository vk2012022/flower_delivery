from telegram.ext import ApplicationBuilder, CommandHandler
from telegram_bot.handlers import start, order, order_flower, orders_from_site, orders_from_telegram
from django.core.management.base import BaseCommand
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **kwargs):
        application = ApplicationBuilder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("order", order))
        application.add_handler(CommandHandler("order_flower", order_flower))
        application.add_handler(CommandHandler("orders_from_site", orders_from_site))
        application.add_handler(CommandHandler("orders_from_telegram", orders_from_telegram))

        application.run_polling()
