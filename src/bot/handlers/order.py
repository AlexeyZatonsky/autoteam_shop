from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from datetime import datetime, date, timedelta
import uuid

from ..api.order_api import OrderAPI
from ..keyboards.order import (
    get_order_management_menu,
    get_order_list_keyboard,
    get_order_view_keyboard,
    get_order_status_keyboard,
    get_payment_status_keyboard,
    get_order_cancel_confirmation_keyboard,
    get_order_delete_confirmation_keyboard,
    get_delete_completed_confirmation_keyboard
)
from ..states.order import OrderStates
from ...orders.enums import OrderStatusEnum, PaymentStatusEnum


router = Router()


# Обработчики меню заказов

@router.callback_query(F.data == "order:manage")
async def order_management(callback: CallbackQuery, **kwargs):
    """Обработчик кнопки управления заказами"""
    keyboard = get_order_management_menu()
    await callback.message.edit_text(
        "📋 Управление заказами:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "order:all")
async def get_all_orders(callback: CallbackQuery, **data):
    """Получение списка всех заказов"""
    api_client = data["api_client"].order_api
    
    await callback.answer("Загрузка списка заказов...")
    
    try:
        orders = await api_client.get_all_orders()
        if not orders:
            await callback.message.edit_text(
                "📋 Заказы не найдены",
                reply_markup=get_order_management_menu()
            )
            return
        
        keyboard = get_order_list_keyboard(orders)
        await callback.message.edit_text(
            "📋 Список всех заказов:\n\n"
            "Формат: 👤 Пользователь | 💵 Сумма | 📊 Статус заказа | 💰 Статус оплаты",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )


@router.callback_query(F.data == "order:today")
async def get_today_orders(callback: CallbackQuery, **data):
    """Получение списка заказов за сегодня"""
    api_client = data["api_client"].order_api
    
    await callback.answer("Загрузка заказов за сегодня...")
    
    try:
        orders = await api_client.get_today_orders()
        if not orders:
            await callback.message.edit_text(
                "📋 Заказы за сегодня не найдены",
                reply_markup=get_order_management_menu()
            )
            return
        
        keyboard = get_order_list_keyboard(orders)
        await callback.message.edit_text(
            "📋 Заказы за сегодня:\n\n"
            "Формат: 👤 Пользователь | 💵 Сумма | 📊 Статус заказа | 💰 Статус оплаты",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )


@router.callback_query(F.data == "order:week")
async def get_week_orders(callback: CallbackQuery, **data):
    """Получение списка заказов за неделю"""
    api_client = data["api_client"].order_api
    
    await callback.answer("Загрузка заказов за неделю...")
    
    try:
        orders = await api_client.get_week_orders()
        if not orders:
            await callback.message.edit_text(
                "📋 Заказы за неделю не найдены",
                reply_markup=get_order_management_menu()
            )
            return
        
        keyboard = get_order_list_keyboard(orders)
        await callback.message.edit_text(
            "📋 Заказы за последнюю неделю:\n\n"
            "Формат: 👤 Пользователь | 💵 Сумма | 📊 Статус заказа | 💰 Статус оплаты",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )


@router.callback_query(F.data == "order:completed")
async def get_completed_orders(callback: CallbackQuery, **data):
    """Получение списка завершенных заказов"""
    api_client = data["api_client"].order_api
    
    await callback.answer("Загрузка завершенных заказов...")
    
    try:
        orders = await api_client.get_completed_orders()
        if not orders:
            await callback.message.edit_text(
                "📋 Завершенные заказы не найдены",
                reply_markup=get_order_management_menu()
            )
            return
        
        keyboard = get_order_list_keyboard(orders)
        await callback.message.edit_text(
            "📋 Завершенные заказы:\n\n"
            "Формат: 👤 Пользователь | 💵 Сумма | 📊 Статус заказа | 💰 Статус оплаты",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )


# Обработчики поиска заказов

@router.callback_query(F.data == "order:search_by_id")
async def search_by_id_start(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Начало поиска заказа по ID"""
    await state.set_state(OrderStates.waiting_for_order_id)
    await callback.message.edit_text(
        "🔍 Введите ID заказа:",
        reply_markup=None
    )
    await callback.answer()


@router.message(OrderStates.waiting_for_order_id)
async def search_by_id_process(message: Message, state: FSMContext, **data):
    """Обработка ввода ID заказа"""
    api_client = data["api_client"].order_api
    order_id = message.text.strip()
    
    try:
        # Пытаемся преобразовать введенный текст в UUID
        order_id_uuid = uuid.UUID(order_id)
        order = await api_client.get_order(order_id_uuid)
        
        # Формируем текст с информацией о заказе
        order_text = format_order_details(order)
        
        # Отправляем информацию о заказе
        keyboard = get_order_view_keyboard(order_id)
        await message.answer(
            order_text,
            reply_markup=keyboard
        )
    except ValueError:
        await message.answer(
            "❌ Некорректный формат ID заказа. Пожалуйста, введите правильный ID.",
            reply_markup=get_order_management_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при поиске заказа: {str(e)}",
            reply_markup=get_order_management_menu()
        )
    
    # Сбрасываем состояние
    await state.clear()


@router.callback_query(F.data == "order:search_by_username")
async def search_by_username_start(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Начало поиска заказов по имени пользователя"""
    await state.set_state(OrderStates.waiting_for_username)
    await callback.message.edit_text(
        "🔍 Введите имя пользователя в Telegram (без @):",
        reply_markup=None
    )
    await callback.answer()


@router.message(OrderStates.waiting_for_username)
async def search_by_username_process(message: Message, state: FSMContext, **data):
    """Обработка ввода имени пользователя"""
    api_client = data["api_client"].order_api
    username = message.text.strip()
    
    if username.startswith('@'):
        username = username[1:]
    
    try:
        orders = await api_client.get_orders_by_username(username)
        
        if not orders:
            await message.answer(
                f"📋 Заказы пользователя @{username} не найдены",
                reply_markup=get_order_management_menu()
            )
        else:
            keyboard = get_order_list_keyboard(orders)
            await message.answer(
                f"📋 Заказы пользователя @{username}:\n\n"
                f"Формат: 👤 Пользователь | 💵 Сумма | 📊 Статус заказа | 💰 Статус оплаты",
                reply_markup=keyboard
            )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при поиске заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )
    
    # Сбрасываем состояние
    await state.clear()


# Обработчики просмотра и управления заказом

@router.callback_query(F.data.startswith("order:view:"))
async def view_order(callback: CallbackQuery, **data):
    """Просмотр информации о заказе"""
    api_client = data["api_client"].order_api
    order_id = callback.data.split(":")[2]
    
    await callback.answer("Загрузка информации о заказе...")
    
    try:
        order = await api_client.get_order(order_id)
        
        # Формируем текст с информацией о заказе
        order_text = format_order_details(order)
        
        # Отправляем информацию о заказе
        keyboard = get_order_view_keyboard(order_id)
        await callback.message.edit_text(
            order_text,
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении информации о заказе: {str(e)}",
            reply_markup=get_order_management_menu()
        )


@router.callback_query(F.data.startswith("order:change_status:"))
async def change_status_start(callback: CallbackQuery, **kwargs):
    """Начало изменения статуса заказа"""
    order_id = callback.data.split(":")[2]
    
    keyboard = get_order_status_keyboard(order_id)
    await callback.message.edit_text(
        "✏️ Выберите новый статус заказа:",
        reply_markup=keyboard
    )
    await callback.answer()


async def get_full_order_id(api_client, short_order_id: str) -> str:
    """Получает полный UUID заказа по его короткой версии"""
    orders = await api_client.get_all_orders()
    for order in orders:
        if order["id"].startswith(short_order_id):
            return order["id"]
    raise ValueError(f"Заказ с ID {short_order_id} не найден")

@router.callback_query(F.data.startswith("order:set_status:"))
async def set_status(callback: CallbackQuery, **data):
    """Установка нового статуса заказа"""
    api_client = data["api_client"].order_api
    parts = callback.data.split(":")
    short_order_id = parts[2]
    status_name = parts[3]
    
    # Получаем значение перечисления по имени
    status_value = OrderStatusEnum[status_name].value
    
    await callback.answer(f"Изменение статуса заказа на {status_value}...")
    
    try:
        # Получаем полный UUID заказа
        full_order_id = await get_full_order_id(api_client, short_order_id)
        
        # Отправляем значение перечисления, а не его имя, используя полный ID
        await api_client.update_order_status(full_order_id, status_value)
        
        # Получаем обновленную информацию о заказе
        order = await api_client.get_order(full_order_id)
        
        # Формируем текст с информацией о заказе
        order_text = format_order_details(order)
        
        # Отправляем информацию о заказе
        keyboard = get_order_view_keyboard(full_order_id)
        await callback.message.edit_text(
            f"✅ Статус заказа изменен на {status_value}\n\n{order_text}",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при изменении статуса заказа: {str(e)}",
            reply_markup=get_order_view_keyboard(short_order_id)
        )


@router.callback_query(F.data.startswith("order:change_payment:"))
async def change_payment_start(callback: CallbackQuery, **kwargs):
    """Начало изменения статуса оплаты заказа"""
    order_id = callback.data.split(":")[2]
    
    keyboard = get_payment_status_keyboard(order_id)
    await callback.message.edit_text(
        "💰 Выберите новый статус оплаты заказа:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:set_payment:"))
async def set_payment(callback: CallbackQuery, **data):
    """Установка нового статуса оплаты заказа"""
    api_client = data["api_client"].order_api
    parts = callback.data.split(":")
    short_order_id = parts[2]
    payment_status_name = parts[3]
    
    # Получаем значение перечисления по имени
    payment_status_value = PaymentStatusEnum[payment_status_name].value
    
    await callback.answer(f"Изменение статуса оплаты на {payment_status_value}...")
    
    try:
        # Получаем полный UUID заказа
        full_order_id = await get_full_order_id(api_client, short_order_id)
        
        # Отправляем значение перечисления, а не его имя
        await api_client.update_payment_status(full_order_id, payment_status_value)
        
        # Получаем обновленную информацию о заказе
        order = await api_client.get_order(full_order_id)
        
        # Формируем текст с информацией о заказе
        order_text = format_order_details(order)
        
        # Отправляем информацию о заказе
        keyboard = get_order_view_keyboard(full_order_id)
        await callback.message.edit_text(
            f"✅ Статус оплаты изменен на {payment_status_value}\n\n{order_text}",
            reply_markup=keyboard
        )
    except Exception as e:
        # В случае ошибки используем короткий ID для клавиатуры
        await callback.message.edit_text(
            f"❌ Ошибка при изменении статуса оплаты: {str(e)}",
            reply_markup=get_order_management_menu()
        )


@router.callback_query(F.data.startswith("order:confirm_cancel:"))
async def confirm_cancel_order(callback: CallbackQuery, **kwargs):
    """Подтверждение отмены заказа"""
    order_id = callback.data.split(":")[2]
    
    keyboard = get_order_cancel_confirmation_keyboard(order_id)
    await callback.message.edit_text(
        "❓ Вы уверены, что хотите отменить заказ?\n\n"
        "Это действие изменит статус заказа на 'Отменён'.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:cancel:"))
async def cancel_order(callback: CallbackQuery, **data):
    """Отмена заказа"""
    api_client = data["api_client"].order_api
    short_order_id = callback.data.split(":")[2]
    
    await callback.answer("Отмена заказа...")
    
    try:
        # Получаем полный UUID заказа
        full_order_id = await get_full_order_id(api_client, short_order_id)
        
        # Устанавливаем статус CANCELLED
        await api_client.update_order_status(full_order_id, "CANCELLED")
        
        # Получаем обновленную информацию о заказе
        order = await api_client.get_order(full_order_id)
        
        # Формируем текст с информацией о заказе
        order_text = format_order_details(order)
        
        # Отправляем информацию о заказе
        keyboard = get_order_view_keyboard(full_order_id)
        await callback.message.edit_text(
            f"✅ Заказ успешно отменен\n\n{order_text}",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при отмене заказа: {str(e)}",
            reply_markup=get_order_view_keyboard(short_order_id)
        )


@router.callback_query(F.data.startswith("order:confirm_delete:"))
async def confirm_delete_order(callback: CallbackQuery, **kwargs):
    """Подтверждение удаления заказа"""
    order_id = callback.data.split(":")[2]
    
    keyboard = get_order_delete_confirmation_keyboard(order_id)
    await callback.message.edit_text(
        "❗ Вы уверены, что хотите удалить заказ?\n\n"
        "Это действие нельзя отменить. Заказ будет полностью удален из базы данных.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:delete:"))
async def delete_order(callback: CallbackQuery, **data):
    """Удаление заказа"""
    api_client = data["api_client"].order_api
    short_order_id = callback.data.split(":")[2]
    
    await callback.answer("Удаление заказа...")
    
    try:
        # Получаем полный UUID заказа
        full_order_id = await get_full_order_id(api_client, short_order_id)
        
        await api_client.delete_order(full_order_id)
        
        await callback.message.edit_text(
            "✅ Заказ успешно удален",
            reply_markup=get_order_management_menu()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении заказа: {str(e)}",
            reply_markup=get_order_management_menu()
        )


@router.callback_query(F.data == "order:delete_completed")
async def confirm_delete_completed(callback: CallbackQuery, **kwargs):
    """Подтверждение удаления всех завершенных заказов"""
    keyboard = get_delete_completed_confirmation_keyboard()
    await callback.message.edit_text(
        "❗ Вы уверены, что хотите удалить ВСЕ завершенные заказы?\n\n"
        "Это действие нельзя отменить. Все завершенные заказы будут полностью удалены из базы данных.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "order:delete_completed_confirm")
async def delete_completed_orders(callback: CallbackQuery, **data):
    """Удаление всех завершенных заказов"""
    api_client = data["api_client"].order_api
    
    await callback.answer("Удаление завершенных заказов...")
    
    try:
        result = await api_client.delete_completed_orders()
        count = result.get("count", 0)
        
        await callback.message.edit_text(
            f"✅ Успешно удалено {count} завершенных заказов",
            reply_markup=get_order_management_menu()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении завершенных заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )


# Вспомогательные функции

def format_order_details(order: dict) -> str:
    """Форматирует информацию о заказе для отображения"""
    order_id = order.get("id", "Неизвестно")
    status = order.get("status", "Неизвестно").upper() if order.get("status") else "Неизвестно"
    payment_status = order.get("payment_status", "Неизвестно").upper() if order.get("payment_status") else "Неизвестно"
    payment_method = order.get("payment_method", "Неизвестно").upper() if order.get("payment_method") else "Неизвестно"
    total_amount = order.get("total_amount", "0")
    created_at = order.get("created_at", "Неизвестно")
    delivery_method = order.get("delivery_method", "Неизвестно").upper() if order.get("delivery_method") else "Неизвестно"
    phone_number = order.get("phone_number", "Не указан")
    delivery_address = order.get("delivery_address", "Не указан")
    telegram_username = order.get("telegram_username", "Неизвестно")
    full_name = order.get("full_name", "Не указано")
    
    # Форматируем дату создания
    if isinstance(created_at, str):
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_at = dt.strftime("%d.%m.%Y %H:%M")
        except:
            pass
    
    # Получаем список товаров
    items = order.get("items", [])
    items_text = ""
    for i, item in enumerate(items, 1):
        product_name = item.get("product_name", "Неизвестный товар")
        quantity = item.get("quantity", 0)
        price = item.get("price", 0)
        items_text += f"{i}. {product_name} x {quantity} = {float(price) * quantity}₽\n"
    
    # Формируем текст
    text = (
        f"🛍 Заказ #{order_id[:8]}\n\n"
        f"📅 Дата создания: {created_at}\n"
        f"👤 Пользователь: @{telegram_username}\n"
        f"👥 Получатель: {full_name}\n"
        f"📱 Телефон: {phone_number}\n"
        f"🚚 Способ доставки: {delivery_method}\n"
        f"📍 Адрес доставки: {delivery_address}\n"
        f"💳 Способ оплаты: {payment_method}\n"
        f"💰 Статус оплаты: {payment_status}\n"
        f"📊 Статус заказа: {status}\n"
        f"💵 Сумма заказа: {total_amount}₽\n\n"
        f"📦 Товары в заказе:\n{items_text}"
    )
    
    return text


# Обработчики навигации

@router.callback_query(F.data.startswith("order:page:"))
async def handle_pagination(callback: CallbackQuery, **data):
    """Обработчик пагинации списка заказов"""
    api_client = data["api_client"].order_api
    page = int(callback.data.split(":")[2])
    
    # Получаем текущий список заказов из состояния
    # В реальном приложении здесь нужно будет сохранять текущий список заказов в состоянии
    # или делать новый запрос к API
    
    # Для примера просто получим все заказы
    try:
        orders = await api_client.get_all_orders(skip=page * 5, limit=5)
        
        if not orders:
            await callback.message.edit_text(
                "📋 Заказы не найдены на этой странице",
                reply_markup=get_order_management_menu()
            )
            return
        
        keyboard = get_order_list_keyboard(orders, page=page)
        await callback.message.edit_text(
            "📋 Список заказов:\n\n"
            "Формат: 👤 Пользователь | 💵 Сумма | 📊 Статус заказа | 💰 Статус оплаты",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении заказов: {str(e)}",
            reply_markup=get_order_management_menu()
        )
    
    await callback.answer()


@router.callback_query(F.data == "order:refresh")
async def refresh_orders(callback: CallbackQuery, **data):
    """Обновление списка заказов"""
    # Просто вызываем обработчик для получения всех заказов
    await get_all_orders(callback, **data)


@router.callback_query(F.data == "order:back_to_list")
async def back_to_list(callback: CallbackQuery, **data):
    """Возврат к списку заказов"""
    # Просто вызываем обработчик для получения всех заказов
    await get_all_orders(callback, **data)


@router.callback_query(F.data == "order:noop")
async def noop(callback: CallbackQuery, **kwargs):
    """Обработчик для кнопок без действия"""
    await callback.answer()


@router.callback_query(F.data.startswith("order:user_info:"))
async def user_info(callback: CallbackQuery, **data):
    """Просмотр информации о пользователе, сделавшем заказ"""
    api_client = data["api_client"].order_api
    order_id = callback.data.split(":")[2]
    
    await callback.answer("Загрузка информации о пользователе...")
    
    try:
        # Получаем информацию о заказе
        order = await api_client.get_order(order_id)
        
        if not order:
            await callback.message.edit_text(
                "❌ Заказ не найден",
                reply_markup=get_order_management_menu()
            )
            return
        
        # Получаем имя пользователя из заказа
        username = order.get("telegram_username")
        user_id = order.get("user_id")
        
        if not username and not user_id:
            await callback.message.edit_text(
                "❌ Информация о пользователе отсутствует в заказе",
                reply_markup=get_order_view_keyboard(order_id)
            )
            return
        
        # Формируем базовую информацию о пользователе из заказа
        user_text = format_basic_user_info(order)
        
        # Пытаемся получить детальную информацию о пользователе
        try:
            if username:
                user_info = await api_client.get_user_info(username)
                if user_info:
                    # Формируем текст с информацией о пользователе
                    user_text = format_user_info(user_info, order)
        except Exception as e:
            # Если не удалось получить детальную информацию, используем базовую
            user_text += f"\n\n⚠️ Не удалось получить полную информацию: {str(e)}"
        
        # Отправляем информацию о пользователе
        await callback.message.edit_text(
            f"ℹ️ Информация о пользователе:\n\n{user_text}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 К заказу", 
                        callback_data=f"order:view:{order_id}"
                    )
                ]
            ])
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении информации о пользователе: {str(e)}",
            reply_markup=get_order_management_menu()
        )


def format_user_info(user_info: dict, order: dict) -> str:
    """Форматирует полную информацию о пользователе для отображения"""
    username = user_info.get("tg_name", order.get("telegram_username", "Неизвестно"))
    tg_first_name = user_info.get("first_name", "")
    tg_last_name = user_info.get("last_name", "")
    tg_full_name = f"{tg_first_name} {tg_last_name}".strip() or "Не указано"
    recipient_name = order.get("full_name", "Не указано")
    email = user_info.get("email", "Не указан")
    phone = order.get("phone_number", "Не указан")
    address = order.get("delivery_address", "Не указан")
    
    # Получаем статистику заказов
    orders_count = user_info.get("orders_count", 0)
    total_spent = user_info.get("total_spent", 0)
    
    # Формируем текст
    text = (
        f"👤 Пользователь: @{username}\n"
        f"📝 Имя пользователя в Telegram: {tg_full_name}\n"
        f"📝 Имя получателя: {recipient_name}\n"
        f"📧 Email: {email}\n"
        f"📱 Телефон: {phone}\n"
        f"📍 Адрес доставки: {address}\n\n"
        f"📊 Статистика:\n"
        f"- Количество заказов: {orders_count}\n"
        f"- Общая сумма заказов: {total_spent}₽\n"
    )
    
    return text


def format_basic_user_info(order: dict) -> str:
    """Форматирует базовую информацию о пользователе из заказа"""
    username = order.get("telegram_username", "Неизвестно")
    user_id = order.get("user_id", "Неизвестно")
    recipient_name = order.get("full_name", "Не указано")
    phone = order.get("phone_number", "Не указан")
    address = order.get("delivery_address", "Не указан")
    
    # Формируем текст
    text = (
        f"👤 Пользователь: @{username}\n"
        f"🆔 ID пользователя: {user_id}\n"
        f"📝 Имя получателя: {recipient_name}\n"
        f"📱 Телефон: {phone}\n"
        f"📍 Адрес доставки: {address}\n"
    )
    
    return text 