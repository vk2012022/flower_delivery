import time
import logging
import asyncio
from django.core.management.base import BaseCommand
from telegram_bot.admin_bot import check_new_orders, notify_admin

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск бота администратора для уведомления о новых заказах'

    def handle(self, *args, **kwargs):
        logger.info("Запуск нового бота администратора...")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start_bot())

    async def start_bot(self):
        message = "Бот администратора запущен!"
        await notify_admin(message)
        while True:
            logger.info("Проверка новых заказов с сайта и Telegram")
            await check_new_orders()  # Асинхронный вызов функции
            await asyncio.sleep(300)  # Асинхронная задержка на 5 минут
