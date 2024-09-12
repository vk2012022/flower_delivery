import os
import django
import asyncio
import logging
from telegram.ext import Application, CommandHandler
from telegram.error import Conflict  # Импортируем ошибку Conflict
from telegram_bot.handlers import start, order, order_flower
import time  # Для ожидания

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Логируем начало работы скрипта
logging.debug("Запуск bot.py")

# Устанавливаем переменную окружения для указания настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')
django.setup()
logging.debug("Django успешно инициализирован")

async def main():
    try:
        logging.debug("Создаем приложение Telegram бота")
        application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
        logging.debug("Приложение Telegram бота создано")

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("order", order))
        application.add_handler(CommandHandler("order_flower", order_flower))
        logging.debug("Обработчики команд добавлены")

        # Попытка запустить бота с ожиданием в случае конфликта
        while True:
            try:
                logging.debug("Запуск бота через run_polling")
                await application.run_polling()
                logging.debug("Бот завершил работу")
                break  # Если бот успешно запустился, выходим из цикла

            except Conflict:
                logging.error("Конфликт: бот уже запущен другим процессом. Ожидание...")
                time.sleep(10)  # Ждем 10 секунд перед повторной попыткой

    except Exception as e:
        logging.error(f"Ошибка во время работы бота: {e}")
        raise

if __name__ == '__main__':
    logging.debug("Запуск main()")
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Ошибка при запуске main: {e}")
