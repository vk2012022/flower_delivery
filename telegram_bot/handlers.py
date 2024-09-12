import logging  # Импортируем модуль логирования
from telegram import Update
from telegram.ext import CallbackContext
from orders.models import Flower, Order, AdminSettings
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

WORKING_HOURS_START = 9
WORKING_HOURS_END = 18


def is_working_hours():
    now = datetime.now().time()
    return WORKING_HOURS_START <= now.hour < WORKING_HOURS_END


async def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    try:
        settings = await sync_to_async(AdminSettings.objects.get)(id=1)

        # Приведение обоих значений к одному типу перед сравнением
        is_admin_result = str(settings.admin_telegram_id) == str(user_id)

        # Логируем результат проверки
        logging.info(
            f"Проверка прав администратора: user_id={user_id}, admin_telegram_id={settings.admin_telegram_id}, is_admin={is_admin_result}")

        return is_admin_result
    except AdminSettings.DoesNotExist:
        logging.error("Ошибка: AdminSettings не найден.")
        return False


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Добро пожаловать! Чтобы заказать цветы, используйте команду /order. '
                                    'Для установки администратора используйте /setadmin. '
                                    'Для получения заказов с сайта используйте /orders_from_site. '
                                    'Для получения заказов через Telegram используйте /orders_from_telegram.')


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
        await notify_admin(
            f"Новый заказ на {flower.name} ({quantity} шт.) через Telegram от {telegram_username} (ID: {telegram_user_id})!",
            context)
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID цветка и количество.")
    except Flower.DoesNotExist:
        await update.message.reply_text("Такого цветка не существует.")


async def set_admin(update: Update, context: CallbackContext) -> None:
    admin_id = update.message.from_user.id
    settings, created = await sync_to_async(AdminSettings.objects.get_or_create)(id=1)
    settings.admin_telegram_id = admin_id
    await sync_to_async(settings.save)()

    # Логируем ID администратора для проверки
    logging.info(f"Установлен новый администратор с ID: {admin_id}")

    await update.message.reply_text(f"Администратор успешно установлен с ID: {admin_id}")
    await notify_admin(f"Администратор установлен с ID: {admin_id}", context)


async def orders_from_site(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /orders_from_site для получения заказов за период"""
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("Эта команда доступна только администраторам.")
        return

    try:
        # Аргументы даты (если переданы)
        start_date_str = context.args[0] if len(context.args) > 0 else None
        end_date_str = context.args[1] if len(context.args) > 1 else None

        # Парсим даты (если не переданы, используем None)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

        # Если указана конечная дата, добавляем конец дня (23:59:59) и делаем её aware
        if end_date:
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        # Делаем start_date "aware", если она указана
        if start_date:
            start_date = timezone.make_aware(start_date)

        # Фильтруем заказы по дате создания, если указаны даты
        orders_query = Order.objects.filter(is_from_telegram=False).order_by('created_at')
        if start_date:
            orders_query = orders_query.filter(created_at__gte=start_date)
        if end_date:
            orders_query = orders_query.filter(created_at__lte=end_date)

        site_orders = await sync_to_async(list)(orders_query)

        if site_orders:
            current_day = None
            message = ""
            messages = []

            for order in site_orders:
                order_date = order.created_at.date()  # Получаем дату создания заказа

                if current_day != order_date:
                    if message:  # Если сообщение не пустое, добавляем его в список для отправки
                        messages.append(message)
                    # Создаем новое сообщение для нового дня
                    message = f"Заказы за {order_date}:\n"
                    current_day = order_date

                # Добавляем информацию о заказе
                message += f"Заказ ID: {order.id}, Описание: {order.description}\n"

                # Проверяем длину сообщения и разбиваем его при необходимости
                if len(message) > 4000:
                    messages.append(message)
                    message = ""

            # Добавляем последнее сообщение, если оно не пустое
            if message:
                messages.append(message)

            # Отправляем все сообщения админу
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
    """Обработчик команды /orders_from_telegram для получения заказов за период"""
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("Эта команда доступна только администраторам.")
        return

    try:
        # Аргументы даты (если переданы)
        start_date_str = context.args[0] if len(context.args) > 0 else None
        end_date_str = context.args[1] if len(context.args) > 1 else None

        # Парсим даты (если не переданы, используем None)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

        # Если указана конечная дата, добавляем конец дня (23:59:59) и делаем её aware
        if end_date:
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        # Делаем start_date "aware", если она указана
        if start_date:
            start_date = timezone.make_aware(start_date)

        # Фильтруем заказы по дате создания, если указаны даты
        orders_query = Order.objects.filter(is_from_telegram=True).order_by('created_at')
        if start_date:
            orders_query = orders_query.filter(created_at__gte=start_date)
        if end_date:
            orders_query = orders_query.filter(created_at__lte=end_date)

        telegram_orders = await sync_to_async(list)(orders_query)

        if telegram_orders:
            current_day = None
            message = ""
            messages = []

            for order in telegram_orders:
                order_date = order.created_at.date()  # Получаем дату создания заказа

                if current_day != order_date:
                    if message:  # Если сообщение не пустое, добавляем его в список для отправки
                        messages.append(message)
                    # Создаем новое сообщение для нового дня
                    message = f"Заказы за {order_date}:\n"
                    current_day = order_date

                # Добавляем информацию о заказе
                message += f"Заказ ID: {order.id}, Описание: {order.description}\n"

                # Проверяем длину сообщения и разбиваем его при необходимости
                if len(message) > 4000:
                    messages.append(message)
                    message = ""

            # Добавляем последнее сообщение, если оно не пустое
            if message:
                messages.append(message)

            # Отправляем все сообщения админу
            for msg in messages:
                await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Заказы через Telegram отсутствуют за указанный период.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите даты в формате 'YYYY-MM-DD'.")
    except Exception as e:
        logging.error(f"Ошибка при получении заказов через Telegram: {e}")
        await update.message.reply_text("Произошла ошибка при получении заказов через Telegram.")


async def notify_admin(message: str, context: CallbackContext = None) -> None:
    try:
        settings = await sync_to_async(AdminSettings.objects.get)(id=1)
        if settings.admin_telegram_id:
            if context:  # Если контекст передан (вызывается из бота)
                await context.bot.send_message(chat_id=settings.admin_telegram_id, text=message)
            else:
                logging.debug(f"Уведомление админу: {message}")
        else:
            logging.warning("Администратор не настроен для получения уведомлений.")
    except AdminSettings.DoesNotExist:
        logging.error("AdminSettings не существует. Администратор не настроен.")
