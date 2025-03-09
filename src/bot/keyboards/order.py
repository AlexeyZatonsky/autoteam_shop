from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_order_management_menu() -> InlineKeyboardMarkup:
    """Клавиатура управления заказами"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Все заказы", callback_data="order:list"),
                InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="order:search_by_id")
            ],
            [
                InlineKeyboardButton(text="👤 Заказы пользователя", callback_data="order:search_by_user"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="order:stats")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")
            ]
        ]
    )


def get_order_list_keyboard(orders: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком заказов"""
    keyboard = []
    
    # Добавляем кнопки для каждого заказа
    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🛍 Заказ #{order['id']}", 
                callback_data=f"order:view:{order['id']}"
            )
        ])
    
    # Добавляем кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="order:list")
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
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ", 
                    callback_data=f"order:confirm_cancel:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(text="🔙 К списку", callback_data="order:list")
            ]
        ]
    )


def get_order_status_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора статуса заказа"""
    statuses = [
        ("✅ Подтвержден", "confirmed"),
        ("📦 В обработке", "processing"),
        ("🚚 Отправлен", "shipped"),
        ("🏁 Доставлен", "delivered"),
        ("❌ Отменен", "cancelled")
    ]
    
    keyboard = []
    for text, status in statuses:
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"order:set_status:{order_id}:{status}"
            )
        ])
    
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
                    text="🔙 Отмена", 
                    callback_data=f"order:view:{order_id}"
                )
            ]
        ]
    ) 