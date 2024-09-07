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
                logger.debug("Начало проверки новых заказов")
                five_minutes_ago = now() - timedelta(minutes=5)
                logger.debug(f"Ищем заказы, созданные после: {five_minutes_ago}")

                # Получаем заказы за последние 5 минут
                new_orders = await sync_to_async(list)(Order.objects.filter(created_at__gte=five_minutes_ago))
                logger.debug(f"Найдено новых заказов: {len(new_orders)}")

                if new_orders:  # Если есть новые заказы
                    message = "Новые заказы за последние 5 минут:\n"
                    for order in new_orders:
                        logger.debug(f"Проверка заказа: {order.id}")
                        already_notified = await sync_to_async(NotifiedOrder.objects.filter)(order=order)
                        if not await sync_to_async(already_notified.exists)():
                            # Извлекаем цветы, связанные с заказом
                            flowers = await sync_to_async(list)(order.flowers.all())
                            logger.debug(f"Цветы для заказа {order.id}: {flowers}")

                            flower_info = ", ".join(
                                [f"{flower.name} (ID: {flower.id})" if flower.name else f"ID: {flower.id}" for flower in
                                 flowers])
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

                    flower_info = ", ".join(
                    [f"{flower.name} (ID: {flower.id})" if flower.name else f"ID: {flower.id}" for flower in
                    flowers])
                    flower_info = flower_info if flower_info else "Цветы не указаны"

                    # Добавляем информацию о заказе и цветах в сообщение
                    message += f"Заказ {order.id}: {'Телеграм' if order.is_from_telegram else 'Сайт'}, Цветы: {flower_info}\n"
                    logger.debug(f"Добавление заказа {order.id} в уведомление")

                    # Создаем запись уведомленного заказа
                    await sync_to_async(NotifiedOrder.objects.create)(order=order)







            # Отправляем уведомление админу, только если есть заказы
            if message != "Новые заказы за последние 5 минут:\n":  # Если были добавлены заказы в сообщение
                await notify_admin(message)
            else:
                logger.debug("Нет новых заказов за последние 5 минут.")
        else:
            logger.debug("Новых заказов нет.")

    except Exception as e:
        logger.error(f"Ошибка при проверке новых заказов: {e}")

async def start(update, context):
    """Приветственное сообщение при запуске бота"""
    await update.message.reply_text("Привет, администратор! Я сообщу тебе о новых заказах с сайта и Telegram.")

async def status(update, context):
    """Команда для проверки состояния бота"""
    await update.message.reply_text("Бот работает и проверяет новые заказы каждые 5 минут.")

def start_admin_bot():
    """Запуск бота для администратора"""
    logger.info("Запуск нового бота администратора")

    application = ApplicationBuilder().token(admin_bot_token).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # Запуск бота
    application.run_polling()
