from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from orders import views as orders_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', orders_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='orders/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('order/<int:flower_id>/', orders_views.order, name='order'),
    path('', orders_views.catalog, name='catalog'),  # Главная страница каталога
]
