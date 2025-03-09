from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_product_management_menu() -> InlineKeyboardMarkup:
    """Клавиатура управления продуктами"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Добавить продукт", callback_data="product:add"),
                InlineKeyboardButton(text="📋 Список продуктов", callback_data="product:list")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")
            ]
        ]
    )


def get_product_list_keyboard(products: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком продуктов"""
    keyboard = []
    
    # Добавляем кнопки для каждого продукта
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📦 {product['name']}", 
                callback_data=f"product:view:{product['id']}"
            )
        ])
    
    # Добавляем кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="➕ Добавить", callback_data="product:add"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="product:list")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="product:manage")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_creation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура при создании продукта"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Отмена", callback_data="product:cancel")
            ]
        ]
    )


def get_product_created_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после создания продукта"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 К списку продуктов", callback_data="product:list"),
                InlineKeyboardButton(text="➕ Добавить ещё", callback_data="product:add")
            ],
            [
                InlineKeyboardButton(text="🔙 В меню", callback_data="product:manage")
            ]
        ]
    )


def get_product_view_keyboard(product_id: str) -> InlineKeyboardMarkup:
    """Клавиатура просмотра продукта"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить", 
                    callback_data=f"product:edit:{product_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Удалить", 
                    callback_data=f"product:confirm_delete:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(text="🔙 К списку", callback_data="product:list")
            ]
        ]
    )


def get_product_delete_confirmation_keyboard(product_id: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления продукта"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить", 
                    callback_data=f"product:delete:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Отмена", 
                    callback_data=f"product:view:{product_id}"
                )
            ]
        ]
    ) 