import logging
from telegram import Update
from telegram.ext import CallbackContext
from orders.models import Flower, Order
from datetime import datetime
from django.utils import timezone
from asgiref.sync import sync_to_async
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

NEW_BOT_ADMIN_ID = os.getenv('NEW_BOT_ADMIN_ID')

WORKING_HOURS_START = 9
WORKING_HOURS_END = 18

def is_working_hours():
    now = datetime.now().time()
    return WORKING_HOURS_START <= now.hour < WORKING_HOURS_END

async def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    is_admin_result = str(NEW_BOT_ADMIN_ID) == str(user_id)

    # Логируем результат проверки
    logging.info(
        f"Проверка прав администратора: user_id={user_id}, NEW_BOT_ADMIN_ID={NEW_BOT_ADMIN_ID}, is_admin={is_admin_result}"
    )

    return is_admin_result

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Добро пожаловать! Чтобы заказать цветы, используйте команду /order. '
        'КОМАНДЫ АДМИНИСТРАТОРА! Для получения заказов с сайта используйте /orders_from_site. '
        'Для получения заказов через Telegram используйте /orders_from_telegram. '
        'Вы можете задать период для команды /orders_from_site или /orders_from_telegram, указав даты в формате '
        'YYYY-MM-DD, например: /orders_from_telegram 2024-09-09 2024-09-12.'
    )

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
        flower_id = int(context.args[0])
        quantity = int(context.args[1])
        flower = await sync_to_async(Flower.objects.get)(id=flower_id)

        telegram_user_id = update.message.from_user.id
        telegram_username = update.message.from_user.username or 'unknown'
        description = f"Заказ через Telegram от пользователя: {telegram_username} (ID: {telegram_user_id}), {flower.name} количество: {quantity}"

        new_order = await sync_to_async(Order.objects.create)(
            is_from_telegram=True,
            description=description
        )
        await sync_to_async(new_order.flowers.add)(flower)
        await sync_to_async(new_order.save)()

        await update.message.reply_text(f"Заказ на {flower.name} в количестве {quantity} успешно оформлен!")

        # Уведомление для администратора удалено
        # await notify_admin(f"Новый заказ на {flower.name} ({quantity} шт.) через Telegram от {telegram_username} (ID: {telegram_user_id})!", context)
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID цветка и количество.")
    except Flower.DoesNotExist:
        await update.message.reply_text("Такого цветка не существует.")

async def orders_from_site(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("Эта команда доступна только администраторам.")
        return

    try:
        today = timezone.now().date()

        start_date_str = context.args[0] if len(context.args) > 0 else str(today)
        end_date_str = context.args[1] if len(context.args) > 1 else str(today)

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        start_date = timezone.make_aware(start_date)

        orders_query = Order.objects.filter(is_from_telegram=False).order_by('created_at')
        orders_query = orders_query.filter(created_at__gte=start_date, created_at__lte=end_date)

        site_orders = await sync_to_async(list)(orders_query)

        if site_orders:
            current_day = None
            message = ""
            messages = []

            for order in site_orders:
                order_date = order.created_at.date()

                if current_day != order_date:
                    if message:
                        messages.append(message)
                    message = f"Заказы за {order_date}:\n"
                    current_day = order_date

                message += f"Заказ ID: {order.id}, Описание: {order.description}\n"

                if len(message) > 4000:
                    messages.append(message)
                    message = ""

            if message:
                messages.append(message)

            for msg in messages:
                await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Заказы с сайта отсутствуют за указанный период.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите даты в формате 'YYYY-MM-DD'.")
    except Exception as e:
        logging.error(f"Ошибка при получении заказов с сайта: {e}")
        await update.message.reply_text("Произошла ошибка при получении заказов с сайта.")

async def orders_from_telegram(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("Эта команда доступна только администраторам.")
        return

    try:
        today = timezone.now().date()

        start_date_str = context.args[0] if len(context.args) > 0 else str(today)
        end_date_str = context.args[1] if len(context.args) > 1 else str(today)

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        start_date = timezone.make_aware(start_date)

        orders_query = Order.objects.filter(is_from_telegram=True).order_by('created_at')
        orders_query = orders_query.filter(created_at__gte=start_date, created_at__lte=end_date)

        telegram_orders = await sync_to_async(list)(orders_query)

        if telegram_orders:
            current_day = None
            message = ""
            messages = []

            for order in telegram_orders:
                order_date = order.created_at.date()

                if current_day != order_date:
                    if message:
                        messages.append(message)
                    message = f"Заказы за {order_date}:\n"
                    current_day = order_date

                message += f"Заказ ID: {order.id}, Описание: {order.description}\n"

                if len(message) > 4000:
                    messages.append(message)
                    message = ""

            if message:
                messages.append(message)

            for msg in messages:
                await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Заказы через Telegram отсутствуют за указанный период.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите даты в формате 'YYYY-MM-DD'.")
    except Exception as e:
        logging.error(f"Ошибка при получении заказов через Telegram: {e}")
        await update.message.reply_text("Произошла ошибка при получении заказов через Telegram.")
