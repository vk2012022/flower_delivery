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
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
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
        order = Order.objects.create(user=request.user)
        order.flowers.add(flower)
        order.save()
        messages.success(request, 'Ваш заказ был успешно создан!')
        return redirect('catalog')
    return render(request, 'orders/order.html', {'flower': flower})
