from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_category_management_menu() -> InlineKeyboardMarkup:
    """Клавиатура управления категориями"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Добавить категорию", callback_data="category:add"),
                InlineKeyboardButton(text="📋 Список категорий", callback_data="category:list")
            ],
            [
                InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu:main")
            ]
        ]
    )


def get_category_list_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком категорий"""
    keyboard = []
    
    # Добавляем кнопки для каждой категории
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {category['name']}", 
                callback_data=f"category:view:{category['name']}"
            )
        ])
    
    # Добавляем кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="➕ Добавить", callback_data="category:add")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="category:manage")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_creation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура при создании категории"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Отмена", callback_data="category:cancel")
            ]
        ]
    )


def get_category_created_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после создания категории"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 К списку категорий", callback_data="category:list"),
                InlineKeyboardButton(text="➕ Добавить ещё", callback_data="category:add")
            ],
            [
                InlineKeyboardButton(text="🔙 В меню", callback_data="category:manage")
            ]
        ]
    )


def get_category_view_keyboard(category_name: str) -> InlineKeyboardMarkup:
    """Клавиатура просмотра категории"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖼 Изображение",
                    callback_data=f"category:view_image:{category_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить название",
                    callback_data=f"category:edit_name:{category_name}"
                ),
                InlineKeyboardButton(
                    text="🔄 Изменить изображение",
                    callback_data=f"category:edit_image:{category_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Удалить", 
                    callback_data=f"category:confirm_delete:{category_name}"
                )
            ],
            [
                InlineKeyboardButton(text="🔙 К списку", callback_data="category:list")
            ]
        ]
    )


def get_category_delete_confirmation_keyboard(category_name: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления категории"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить", 
                    callback_data=f"category:delete:{category_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Отмена", 
                    callback_data=f"category:view:{category_name}"
                )
            ]
        ]
    )


def get_category_image_view_keyboard(category_name: str) -> InlineKeyboardMarkup:
    """Клавиатура просмотра изображения категории"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Изменить",
                    callback_data=f"category:edit_image:{category_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=f"category:view:{category_name}"
                )
            ]
        ]
    ) 