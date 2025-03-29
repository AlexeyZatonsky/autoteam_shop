from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
from ...orders.enums import OrderStatusEnum, PaymentStatusEnum


def get_order_management_menu() -> InlineKeyboardMarkup:
    """Клавиатура управления заказами"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Все заказы", callback_data="order:all")
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="order:search_by_id"),
                InlineKeyboardButton(text="👤 Поиск по имени", callback_data="order:search_by_username")
            ],
            [
                InlineKeyboardButton(text="📅 Заказы за сегодня", callback_data="order:today"),
                InlineKeyboardButton(text="📆 Заказы за неделю", callback_data="order:week")
            ],
            [
                InlineKeyboardButton(text="✅ Завершённые заказы", callback_data="order:completed"),
                InlineKeyboardButton(text="🗑 Удалить завершённые", callback_data="order:delete_completed")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")
            ]
        ]
    )


def get_order_list_keyboard(orders: List[Dict], page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком заказов"""
    keyboard = []
    
    # Вычисляем общее количество страниц
    total_pages = (len(orders) + page_size - 1) // page_size
    
    # Получаем заказы для текущей страницы
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(orders))
    current_page_orders = orders[start_idx:end_idx]
    
    # Добавляем кнопки для каждого заказа
    for order in current_page_orders:
        order_id = order.get('id', '')
        status = order.get('status', '').upper() if order.get('status') else 'Неизвестно'
        payment_status = order.get('payment_status', '').upper() if order.get('payment_status') else 'Неизвестно'
        total = order.get('total_amount', '0')
        username = order.get('telegram_username', 'Неизвестно')
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"👤 {username} | 💵 {total}₽ | 📊 {status} | 💰 {payment_status}", 
                callback_data=f"order:view:{order_id}"
            )
        ])
    
    # Добавляем кнопки пагинации
    pagination_buttons = []
    
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"order:page:{page-1}")
        )
    
    if total_pages > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="order:noop")
        )
    
    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"order:page:{page+1}")
        )
    
    if pagination_buttons:
        keyboard.append(pagination_buttons)
    
    # Добавляем кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="order:refresh")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="order:manage")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_view_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура просмотра заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить статус", 
                    callback_data=f"order:change_status:{order_id}"
                ),
                InlineKeyboardButton(
                    text="💰 Изменить статус оплаты", 
                    callback_data=f"order:change_payment:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Информация о пользователе", 
                    callback_data=f"order:user_info:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ", 
                    callback_data=f"order:confirm_cancel:{order_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить заказ", 
                    callback_data=f"order:confirm_delete:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(text="🔙 К списку", callback_data="order:back_to_list")
            ]
        ]
    )


def get_order_status_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора статуса заказа"""
    keyboard = []
    
    # Добавляем кнопки для каждого статуса заказа
    for status in OrderStatusEnum:
        # Используем сокращенный идентификатор заказа для уменьшения длины callback_data
        short_order_id = order_id[:8]  # Берем только первые 8 символов UUID
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status.value}",
                callback_data=f"order:set_status:{short_order_id}:{status.name}"
            )
        ])
    
    # Добавляем кнопку возврата
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"order:view:{order_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_status_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора статуса оплаты заказа"""
    keyboard = []
    
    # Добавляем кнопки для каждого статуса оплаты
    for status in PaymentStatusEnum:
        # Используем сокращенный идентификатор заказа для уменьшения длины callback_data
        short_order_id = order_id[:8]  # Берем только первые 8 символов UUID
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status.value}",
                callback_data=f"order:set_payment:{short_order_id}:{status.name}"
            )
        ])
    
    # Добавляем кнопку возврата
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"order:view:{order_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_cancel_confirmation_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения отмены заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, отменить", 
                    callback_data=f"order:cancel:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Нет, вернуться", 
                    callback_data=f"order:view:{order_id}"
                )
            ]
        ]
    )


def get_order_delete_confirmation_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить", 
                    callback_data=f"order:delete:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Нет, вернуться", 
                    callback_data=f"order:view:{order_id}"
                )
            ]
        ]
    )


def get_delete_completed_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления всех завершенных заказов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить все завершенные заказы", 
                    callback_data="order:delete_completed_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Нет, вернуться", 
                    callback_data="order:manage"
                )
            ]
        ]
    ) 