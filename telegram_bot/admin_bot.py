import logging
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
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
        await sync_to_async(bot.send_message)(chat_id=settings.NEW_BOT_ADMIN_ID, text=message)
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
                already_notified = await sync_to_async(NotifiedOrder.objects.filter)(order=order)
                if not await sync_to_async(already_notified.exists)():
                    message += f"Заказ {order.id}: {'Телеграм' if order.is_from_telegram else 'Сайт'}\n"
                    # Создаём запись об уведомленном заказе
                    await sync_to_async(NotifiedOrder.objects.create)(order=order)

            # Отправляем уведомление админу
            await notify_admin(message)
        else:
            logger.debug("Нет новых заказов за последние 5 минут.")

    except Exception as e:
        logger.error(f"Ошибка при проверке новых заказов: {e}")

async def start(update: Update, context: CallbackContext):
    """Приветственное сообщение при запуске бота"""
    logger.debug(f"Получена команда /start от {update.message.from_user.id}")
    await update.message.reply_text("Привет, администратор! Я сообщу тебе о новых заказах с сайта и Telegram.")

async def status(update: Update, context: CallbackContext):
    """Команда для проверки состояния бота"""
    logger.debug(f"Получена команда /status от {update.message.from_user.id}")
    await update.message.reply_text("Бот работает и проверяет новые заказы каждые 5 минут.")

def start_admin_bot():
    """Запуск бота для администратора"""
    logger.info("Запуск нового бота администратора")

    application = ApplicationBuilder().token(admin_bot_token).build()

    # Добавляем обработчики команд
    logger.debug("Регистрация команд /start и /status")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    logger.debug("Бот готов к приёму команд")

    # Запуск бота
    logger.info("Запуск бота через polling")
    application.run_polling()
