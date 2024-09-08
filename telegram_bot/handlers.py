from telegram import Update
from telegram.ext import CallbackContext
from orders.models import Flower, Order
from datetime import datetime
from asgiref.sync import sync_to_async

WORKING_HOURS_START = 9
WORKING_HOURS_END = 18

def is_working_hours():
    now = datetime.now().time()
    return WORKING_HOURS_START <= now.hour < WORKING_HOURS_END

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Добро пожаловать! Чтобы заказать цветы, используйте команду /order.')

async def order(update: Update, context: CallbackContext) -> None:
    if not is_working_hours():
        await update.message.reply_text('Заказы принимаются только в рабочие часы с 9:00 до 18:00.')
        return

    flowers = await sync_to_async(list)(Flower.objects.all())
    if flowers:
        message = "Доступные цветы:\n"
        for flower in flowers:
            message += f"{flower.id}. {flower.name} - {flower.price} руб.\n"
        message += "\nВведите /order_flower [ID цветка] [количество], чтобы заказать."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("На данный момент цветов нет в наличии.")

async def order_flower(update: Update, context: CallbackContext) -> None:
    if not is_working_hours():
        await update.message.reply_text('Заказы принимаются только в рабочие часы с 9:00 до 18:00.')
        return

    try:
        # Получаем ID цветка и количество
        flower_id = int(context.args[0])
        quantity = int(context.args[1])
        flower = await sync_to_async(Flower.objects.get)(id=flower_id)

        # Получаем идентификатор пользователя Telegram
        telegram_user_id = update.message.from_user.id
        telegram_username = update.message.from_user.username or 'unknown'

        # Сохраняем идентификатор пользователя, название цветка и количество цветов в поле description
        description = f"Заказ через Telegram от пользователя: {telegram_username} (ID: {telegram_user_id}), {flower.name} количество: {quantity}"

        # Создаем заказ и сохраняем описание
        new_order = await sync_to_async(Order.objects.create)(
            is_from_telegram=True,
            description=description
        )
        await sync_to_async(new_order.flowers.add)(flower)
        await sync_to_async(new_order.save)()

        await update.message.reply_text(f"Заказ на {flower.name} в количестве {quantity} успешно оформлен!")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID цветка и количество.")
    except Flower.DoesNotExist:
        await update.message.reply_text("Такого цветка не существует.")
