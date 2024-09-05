from django.contrib import admin
from .models import Flower, Order, AdminSettings

admin.site.register(Flower)
admin.site.register(Order)
admin.site.register(AdminSettings)
