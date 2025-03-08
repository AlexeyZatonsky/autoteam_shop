from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types


def get_main_menu() -> types.InlineKeyboardMarkup:
    """Создание клавиатуры главного меню"""
    builder = InlineKeyboardBuilder()
    
    # Управление продуктами
    builder.button(text="Добавить продукт", callback_data="product:add")
    builder.button(text="Удалить продукт", callback_data="product:delete")
    builder.button(text="Выгрузить список продуктов", callback_data="product:list")
    
    # Управление заказами
    builder.button(text="Выгрузить список заказов", callback_data="order:list")
    builder.button(text="Получить заказ по ID", callback_data="order:get_by_id")
    builder.button(text="Получить заказы по user_id", callback_data="order:get_by_user")
    builder.button(text="Изменить статус заказа", callback_data="order:change_status")
    
    # Управление категориями
    builder.button(text="Управление категориями", callback_data="category:manage")
    
    builder.adjust(1)
    return builder.as_markup()


def get_category_management_menu() -> types.InlineKeyboardMarkup:
    """Создание клавиатуры управления категориями"""
    builder = InlineKeyboardBuilder()
    builder.button(text="Список категорий", callback_data="category:list")
    builder.button(text="Добавить категорию", callback_data="category:add")
    builder.button(text="Назад в меню", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def get_category_list_keyboard(categories: list) -> types.InlineKeyboardMarkup:
    """Создание клавиатуры со списком категорий"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=f"📁 {category['name']}", 
            callback_data=f"category:view:{category['name']}"
        )
    
    builder.button(text="◀️ Назад", callback_data="category:manage")
    builder.button(text="➕ Добавить категорию", callback_data="category:add")
    builder.adjust(1)
    return builder.as_markup()


def get_category_creation_keyboard() -> types.InlineKeyboardMarkup:
    """Создание клавиатуры для создания категории"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="category:cancel")
    return builder.as_markup()


def get_category_created_keyboard() -> types.InlineKeyboardMarkup:
    """Создание клавиатуры после успешного создания категории"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список категорий", callback_data="category:list")
    builder.button(text="➕ Добавить ещё", callback_data="category:add")
    builder.button(text="◀️ В меню", callback_data="category:manage")
    builder.adjust(1)
    return builder.as_markup()


def get_category_view_keyboard(category_name: str) -> types.InlineKeyboardMarkup:
    """Создание клавиатуры для просмотра категории"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🗑 Удалить категорию",
        callback_data=f"category:confirm_delete:{category_name}"
    )
    builder.button(text="◀️ Назад к списку", callback_data="category:list")
    builder.adjust(1)
    return builder.as_markup()


def get_category_delete_confirmation_keyboard(category_name: str) -> types.InlineKeyboardMarkup:
    """Создание клавиатуры для подтверждения удаления категории"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, удалить",
        callback_data=f"category:delete:{category_name}"
    )
    builder.button(
        text="❌ Отмена",
        callback_data=f"category:view:{category_name}"
    )
    builder.adjust(2)
    return builder.as_markup() 