from telegram import Update
from telegram.ext import CallbackContext
from orders.models import Flower, Order, AdminSettings
from datetime import datetime

WORKING_HOURS_START = 9
WORKING_HOURS_END = 18

def is_working_hours():
    now = datetime.now().time()
    return WORKING_HOURS_START <= now.hour < WORKING_HOURS_END

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Добро пожаловать! Чтобы заказать цветы, используйте команду /order. '
                                    'Для установки администратора используйте /setadmin.')

async def order(update: Update, context: CallbackContext) -> None:
    if not is_working_hours():
        await update.message.reply_text('Заказы принимаются только в рабочие часы с 9:00 до 18:00.')
        return

    flowers = Flower.objects.all()
    if flowers.exists():
        message = "Доступные цветы:\n"
        for flower in flowers:
            message += f"{flower.id}. {flower.name} - {flower.price} руб.\n"
        message += "\nВведите /order [ID], чтобы заказать."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("На данный момент цветов нет в наличии.")

async def order_flower(update: Update, context: CallbackContext) -> None:
    if not is_working_hours():
        await update.message.reply_text('Заказы принимаются только в рабочие часы с 9:00 до 18:00.')
        return

    try:
        flower_id = int(context.args[0])
        flower = Flower.objects.get(id=flower_id)
        new_order = Order.objects.create(is_from_telegram=True)
        new_order.flowers.add(flower)
        new_order.save()

        await update.message.reply_text(f"Заказ на {flower.name} успешно оформлен!")
        await notify_admin(f"Новый заказ на {flower.name} через Telegram!", context)
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID цветка.")
    except Flower.DoesNotExist:
        await update.message.reply_text("Такого цветка не существует.")

async def set_admin(update: Update, context: CallbackContext) -> None:
    admin_id = update.message.from_user.id
    settings, created = AdminSettings.objects.get_or_create(id=1)
    settings.admin_telegram_id = admin_id
    settings.save()
    await update.message.reply_text(f"Администратор успешно установлен с ID: {admin_id}")
    await notify_admin(f"Администратор установлен с ID: {admin_id}", context)

async def notify_admin(message: str, context: CallbackContext = None) -> None:
    try:
        settings = AdminSettings.objects.get(id=1)
        if settings.admin_telegram_id:
            if context:  # Если контекст передан (вызывается из бота)
                await context.bot.send_message(chat_id=settings.admin_telegram_id, text=message)
            else:
                print(f"Уведомление админу: {message}")  # Логируем уведомление для веб-части
        else:
            print("Администратор не настроен для получения уведомлений.")
    except AdminSettings.DoesNotExist:
        print("AdminSettings не существует. Администратор не настроен.")
