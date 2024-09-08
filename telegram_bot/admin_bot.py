import logging
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from asgiref.sync import sync_to_async
from django.utils.timezone import now, timedelta
from orders.models import Order, NotifiedOrder
from django.conf import settings

# Логирование
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен нового бота администратора
admin_bot_token = settings.NEW_BOT_TOKEN

async def notify_admin(message: str):
    """Функция отправки уведомлений админу"""
    try:
        bot = Bot(token=admin_bot_token)
        # Отправляем сообщение админу напрямую, без sync_to_async
        await bot.send_message(chat_id=settings.NEW_BOT_ADMIN_ID, text=message)
        logger.debug("Сообщение отправлено админу")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления админу: {e}")

async def check_new_orders():
    """Проверка всех новых заказов за последние 5 минут и отправка уведомлений админу"""
    try:
        five_minutes_ago = now() - timedelta(minutes=5)
        # Получаем заказы за последние 5 минут
        new_orders = await sync_to_async(list)(Order.objects.filter(created_at__gte=five_minutes_ago))

        if new_orders:  # Если есть новые заказы
            message = "Новые заказы за последние 5 минут:\n"
            for order in new_orders:
                logger.debug(f"Проверка заказа: {order.id}")
                already_notified = await sync_to_async(NotifiedOrder.objects.filter)(order=order)
                if not await sync_to_async(already_notified.exists)():
                    # Извлекаем цветы, связанные с заказом
                    flowers = await sync_to_async(list)(order.flowers.all())
                    logger.debug(f"Цветы для заказа {order.id}: {flowers}")

                    # Извлекаем количество из description
                    try:
                        quantity = [int(s) for s in order.description.split() if s.isdigit()][0]
                    except IndexError:
                        quantity = "Не указано"

                    # Формируем информацию о цветах и количестве
                    flower_info = ", ".join([f"{flower.name} (ID: {flower.id}), количество: {quantity}" for flower in flowers])
                    flower_info = flower_info if flower_info else "Цветы не указаны"

                    # Добавляем информацию о заказе и цветах в сообщение
                    message += f"Заказ {order.id}: {'Телеграм' if order.is_from_telegram else 'Сайт'}, Цветы: {flower_info}\n"
                    logger.debug(f"Добавление заказа {order.id} в уведомление")

                    # Создаем запись уведомленного заказа
                    await sync_to_async(NotifiedOrder.objects.create)(order=order)

            # Отправляем уведомление админу, если есть новые заказы
            await notify_admin(message)
        else:
            logger.debug("Новых заказов нет.")
    except Exception as e:
        logger.error(f"Ошибка при проверке новых заказов: {e}")
