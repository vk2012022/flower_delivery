import os
import logging
from telegram.ext import Application, CommandHandler
from telegram_bot.handlers import start, order, order_flower

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Основная функция для запуска бота
def main():
    # Получаем токен из переменной окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен. Проверьте файл .env или переменные окружения.")

    # Создаем приложение Telegram бота
    application = Application.builder().token(token).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("order", order))
    application.add_handler(CommandHandler("order_flower", order_flower))

    # Запускаем бота
    logger.info("Запуск бота...")
    application.run_polling()

# Django команда для запуска
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Запуск Telegram бота'

    def handle(self, *args, **kwargs):
        logger.info("Запуск start_bot.py")
        main()
