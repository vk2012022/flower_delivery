from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import Flower, Order


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вы успешно зарегистрировались!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'orders/register.html', {'form': form})


def catalog(request):
    flowers = Flower.objects.all()
    return render(request, 'orders/catalog.html', {'flowers': flowers})


@login_required
def order(request, flower_id):
    flower = Flower.objects.get(id=flower_id)
    if request.method == 'POST':
        # Получаем количество цветов из формы
        quantity = int(request.POST.get('quantity', 1))  # Значение по умолчанию 1

        # Создаем описание заказа с учетом количества
        description = f"Заказ на {flower.name}, количество: {quantity} шт."

        # Создаем заказ и сохраняем информацию
        order = Order.objects.create(
            user=request.user,
            description=description
        )
        order.flowers.add(flower)
        order.save()

        # Сообщение об успешном заказе
        messages.success(request, 'Заказ успешно создан!')

        return redirect('catalog')

    return render(request, 'orders/order.html', {'flower': flower})
