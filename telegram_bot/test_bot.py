import asyncio
from unittest.mock import MagicMock
from django.test import TestCase
from telegram import Update, User, Chat, Message, Bot
from telegram.ext import Application, CallbackContext
from telegram_bot.handlers import order_flower
from orders.models import Flower
from datetime import datetime

class TelegramBotTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = Bot(token='test_token')  # Создаем тестовый бот
        cls.application = Application.builder().token('test_token').build()

    def setUp(self):
        # Создаем объект User для тестирования
        self.user = User(id=12345, first_name="TestUser", is_bot=False)

        # Создаем объект Chat для тестирования
        self.chat = Chat(id=67890, type="private")

        # Создаем тестовый цветок в базе данных
        self.flower = Flower.objects.create(name="Роза", price=100)

        # Используем mock для создания объекта Message
        self.message = MagicMock(spec=Message)
        self.message.message_id = 1
        self.message.date = datetime.now()
        self.message.chat = self.chat
        self.message.from_user = self.user
        self.message.text = "/order_flower 1 5"
        self.message.bot = self.bot  # Привязываем бота

        # Создаем объект Update с объектом Message
        self.update = Update(update_id=1234, message=self.message)

    async def test_order_flower_command(self):
        # Инициализируем контекст с необходимыми аргументами
        context = CallbackContext(application=self.application)
        context.args = [str(self.flower.id), "5"]  # ID цветка и количество

        # Вызов команды order_flower
        await order_flower(self.update, context)

        # Проверяем, что метод reply_text был вызван с правильным сообщением
        expected_reply = f"Заказ на {self.flower.name} в количестве 5 успешно оформлен!"
        self.message.reply_text.assert_called_once_with(expected_reply)
