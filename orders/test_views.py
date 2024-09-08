from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from orders.models import Flower, Order


class OrderViewTestCase(TestCase):

    def setUp(self):
        # Создаем тестового пользователя и цветы
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.flower_rose = Flower.objects.create(name="Роза", price=100)
        self.flower_tulip = Flower.objects.create(name="Тюльпан", price=50)

    def test_order_creation(self):
        # Логинимся как тестовый пользователь
        self.client.login(username='testuser', password='12345')
        flower = self.flower_rose

        # Делаем POST-запрос на создание заказа
        response = self.client.post(reverse('order', args=[flower.id]), {'quantity': 5})

        # Проверяем, что заказ был создан
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.description, "Заказ на Роза, количество: 5 шт.")
        self.assertEqual(order.flowers.first(), flower)

        # Проверяем редирект на каталог после успешного создания заказа
        self.assertRedirects(response, reverse('catalog'))

    def test_catalog_display(self):
        # Проверяем, что каталог отображается с добавленными цветами
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Роза")
        self.assertContains(response, "Тюльпан")
