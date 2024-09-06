from django.db import models
from django.contrib.auth.models import User

class Flower(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    flowers = models.ManyToManyField(Flower)
    description = models.TextField()  # Добавлено поле описания
    created_at = models.DateTimeField(auto_now_add=True)
    is_from_telegram = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} by {self.user.username if self.user and self.user.username else 'Telegram User'}"

class NotifiedOrder(models.Model):
    """Модель для хранения заказов, по которым уже были отправлены уведомления администратору"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    notified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NotifiedOrder for Order {self.order.id}"

class AdminSettings(models.Model):
    admin_telegram_id = models.CharField(max_length=100, blank=True, null=True)
