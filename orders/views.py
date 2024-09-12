from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import sync_and_async_middleware
from asgiref.sync import sync_to_async
from .forms import UserRegisterForm
from .models import Flower, Order


# from telegram_bot.handlers import notify_admin

@sync_and_async_middleware
async def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if await sync_to_async(form.is_valid)():
            await sync_to_async(form.save)()
            await sync_to_async(messages.success)(request, 'Вы успешно зарегистрировались!')
            return await sync_to_async(redirect)('login')
    else:
        form = UserRegisterForm()
    return await sync_to_async(render)(request, 'orders/register.html', {'form': form})


@sync_and_async_middleware
async def catalog(request):
    flowers = await sync_to_async(list)(Flower.objects.all())
    return await sync_to_async(render)(request, 'orders/catalog.html', {'flowers': flowers})


@login_required
@sync_and_async_middleware
async def order(request, flower_id):
    flower = await sync_to_async(Flower.objects.get)(id=flower_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        description = f"Заказ на {flower.name}, количество: {quantity} шт."
        order = await sync_to_async(Order.objects.create)(
            user=request.user,
            description=description
        )
        await sync_to_async(order.flowers.add)(flower)
        await sync_to_async(order.save)()

        # Убираем уведомление для администратора
        # notify_admin(f"Новый заказ на {flower.name} ({quantity} шт.) от {request.user.username}")

        return await sync_to_async(redirect)('catalog')

    return await sync_to_async(render)(request, 'orders/order.html', {'flower': flower})
