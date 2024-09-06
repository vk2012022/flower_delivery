import time
import logging
import asyncio
from django.core.management.base import BaseCommand
from telegram_bot.admin_bot import check_new_orders

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск бота администратора для уведомления о новых заказах'

    def handle(self, *args, **kwargs):
        logger.info("Запуск нового бота администратора...")

        loop = asyncio.get_event_loop()
        while True:
            logger.info("Проверка новых заказов с сайта и Telegram")
            loop.run_until_complete(check_new_orders())  # Асинхронный вызов функции
            time.sleep(300)  # Проверка каждые 5 минут
