from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from ..states.product import ProductStates
from ..keyboards.product import (
    get_product_management_menu,
    get_product_list_keyboard,
    get_product_creation_keyboard,
    get_product_created_keyboard,
    get_product_view_keyboard,
    get_product_delete_confirmation_keyboard
)
from src.products.schemas import ProductCreate
from src.categories.schemas import CategoryRead
from src.aws import s3_client
from decimal import Decimal
from typing import Dict, List
import aiohttp
import io
import uuid
import re
import tempfile
import os
from src.products.services.file_service import FileService

router = Router(name="product")

# Глобальные переменные
_product_data: ProductCreate = None

def get_product_data() -> ProductCreate:
    global _product_data
    if _product_data is None:
        _product_data = ProductCreate()
        print("Создан новый объект ProductCreate")
    return _product_data

def reset_product_data():
    global _product_data
    _product_data = ProductCreate()

@router.callback_query(F.data.startswith("product:"))
async def product_callback_handler(callback: CallbackQuery, state: FSMContext, api_client):
    """Обработчик всех callback-запросов для продуктов"""
    action = callback.data.split(":")[1]
    
    if action == "add":
        reset_product_data()  # Сбрасываем данные при начале создания
        await callback.message.answer("Пожалуйста, введите название продукта:")
        await state.set_state(ProductStates.waiting_for_name)
    elif action == "list":
        await handle_products_list(callback, api_client)
    elif action == "select_category" and await state.get_state() == ProductStates.waiting_for_category:
        await process_product_category(callback, state)
    elif action == "manage":
        # Показываем меню управления продуктами
        await callback.message.edit_text(
            "Управление продуктами",
            reply_markup=get_product_management_menu()
        )
    elif action == "delete":
        # Логика удаления продукта
        pass
    await callback.answer()


@router.message(StateFilter(ProductStates.waiting_for_name))
async def process_product_name(message: Message, state: FSMContext):
    try:
        name = message.text.strip()
        # Проверяем только длину названия
        if len(name) < 2:
            raise ValueError("Название продукта должно содержать минимум 2 символа")
        if len(name) > 100:
            raise ValueError("Название продукта не должно превышать 100 символов")
        
        product_data = get_product_data()
        product_data.name = name
        
        await message.answer("Отлично! Теперь введите описание продукта:")
        await state.set_state(ProductStates.waiting_for_description)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}\nПожалуйста, введите корректное название продукта.")


@router.message(StateFilter(ProductStates.waiting_for_description))
async def process_product_description(message: Message, state: FSMContext, api_client):
    try:
        description = message.text.strip()
        
        product_data = get_product_data()
        product_data.description = description
        
        # Получаем список категорий для выбора
        response = await api_client.make_request(
            method="GET",
            endpoint="api/categories",
            headers={"Accept": "application/json"}
        )
        
        categories = [CategoryRead(**cat) for cat in response]
        
        if not categories:
            await message.answer("Список категорий пуст. Сначала создайте хотя бы одну категорию.")
            await state.clear()
            return
        
        # Создаем клавиатуру с категориями (по одной кнопке в строке)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"product:select_category:{cat.name}")] 
            for cat in categories
        ])
        
        await message.answer(
            "Выберите категорию продукта (можно выбрать только одну):",
            reply_markup=keyboard
        )
        await state.set_state(ProductStates.waiting_for_category)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}\nПожалуйста, введите корректное описание продукта.")
    except Exception as e:
        await message.answer(f"Ошибка при получении списка категорий: {str(e)}")
        await state.clear()


async def process_product_category(callback: CallbackQuery, state: FSMContext):
    try:
        category_name = callback.data.split(":")[-1]
        # Устанавливаем одну категорию в список
        product_data = get_product_data()
        product_data.categories = [category_name]  # Сохраняем как список с одним элементом
        
        await callback.message.edit_text(
            f"Выбрана категория: {category_name}\n"
            "Теперь введите цену продукта (только число):"
        )
        await state.set_state(ProductStates.waiting_for_price)
    except Exception as e:
        await callback.message.answer(f"Ошибка при выборе категории: {str(e)}")
        await state.clear()


@router.message(StateFilter(ProductStates.waiting_for_price))
async def process_product_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip())
        if price <= 0:
            raise ValueError("Цена должна быть больше 0")
        if price > 99999999.99:
            raise ValueError("Цена не может быть больше 99999999.99")
            
        product_data = get_product_data()
        product_data.price = price  # Сохраняем как Decimal
        
        await message.answer("Отлично! Теперь отправьте фотографию продукта:")
        await state.set_state(ProductStates.waiting_for_photo)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}\nПожалуйста, введите корректную цену (только число):")


@router.message(StateFilter(ProductStates.waiting_for_photo), ~Command("done"), ~Command("cancel"))
async def process_product_photo(message: Message, state: FSMContext, api_client):
    """Обрабатывает загрузку фотографий продукта"""
    # Проверяем, что сообщение содержит фото
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фотографию продукта.")
        return
    
    # Получаем данные продукта
    product_data = get_product_data()
    
    # Проверяем, что не превышен лимит фотографий
    if len(product_data.images) >= 6:
        await message.answer("Вы уже загрузили максимальное количество фотографий (6). Нажмите /done для завершения.")
        return
    
    try:
        # Получаем файл фотографии
        photo = message.photo[-1]  # Берем самое большое разрешение
        file = await message.bot.get_file(photo.file_id)
        file_content = await message.bot.download_file(file.file_path)
        
        # Создаем временный файл для загрузки на сервер
        temp_filename = f"image_{len(product_data.images)}.jpg"
        
        # Создаем FormData для отправки файла
        form = aiohttp.FormData()
        form.add_field(
            'file',
            file_content,
            filename=temp_filename,
            content_type='image/jpeg'
        )
        
        # Отправляем запрос на загрузку файла
        response = await api_client.make_request(
            method="POST",
            endpoint="api/upload",
            data=form
        )
        
        if response and 'url' in response:
            # Добавляем URL изображения в данные продукта
            product_data.images.append(response['url'])
            
            # Отправляем сообщение об успешной загрузке
            await message.answer(
                f"Фото #{len(product_data.images)} успешно загружено. "
                f"Вы можете загрузить еще до {6 - len(product_data.images)} фото или нажать /done для завершения."
            )
        else:
            await message.answer("Ошибка при загрузке фото. Пожалуйста, попробуйте еще раз.")
    
    except Exception as e:
        print(f"Ошибка при обработке фото: {str(e)}")
        await message.answer(f"Произошла ошибка при обработке фото: {str(e)}")


async def send_product_to_api(message: Message, state: FSMContext, api_client):
    try:
        print("Начинаем отправку продукта на сервер")
        product_data = get_product_data()
        
        # Проверяем, что все необходимые данные заполнены
        if not product_data.validate_for_api():
            print("Валидация не пройдена")
            await message.answer(
                "Не все данные заполнены корректно. Пожалуйста, проверьте:\n"
                "- Название (минимум 2 символа)\n"
                "- Цена (больше 0)\n"
                "- Категория (должна быть выбрана)\n"
                "- Фотографии (минимум 1 фото)"
            )
            return

        print(f"Валидация пройдена. Имя: {product_data.name}, Цена: {product_data.price}, Категории: {product_data.categories}, Фото: {len(product_data.images)}")
        
        # Создаем multipart/form-data форму
        form = aiohttp.FormData()
        
        # Добавляем основные поля
        form.add_field('name', product_data.name)
        form.add_field('description', product_data.description or "")
        form.add_field('price', str(product_data.price))
        
        # Добавляем категории
        for category in product_data.categories:
            form.add_field('categories', category)
        
        # Добавляем URL изображений
        for image_url in product_data.images:
            form.add_field('images', image_url)
        
        # Отправляем запрос на создание продукта
        print(f"Отправляем запрос с {len(product_data.images)} изображениями")
        
        # Отправляем запрос
        response = await api_client.make_request(
            method="POST",
            endpoint="api/products",
            data=form
        )
        
        print(f"Ответ сервера: {response}")
        
        await message.answer(
            "Продукт успешно создан!",
            reply_markup=get_product_created_keyboard()
        )
        
        # Очищаем данные продукта
        reset_product_data()
        await state.clear()
        
    except Exception as e:
        print(f"Ошибка при создании продукта: {str(e)}")
        await message.answer(f"Ошибка при создании продукта: {str(e)}")
        await state.clear()


async def handle_products_list(callback: CallbackQuery, api_client):
    try:
        products = await api_client.make_request(
            method="GET",
            endpoint="api/products",
            headers={"Accept": "application/json"}
        )
        
        if not products:
            await callback.message.answer("Список продуктов пуст")
            return
            
        response = "Список продуктов:\n\n"
        for product in products:
            response += f"📦 {product['name']}\n"
            response += f"💰 Цена: {product['price']}\n"
            response += f"📝 Описание: {product['description']}\n\n"
            
        await callback.message.answer(response)
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении списка продуктов: {str(e)}")


# Добавляем обработчик для отмены создания продукта
@router.message(Command("cancel"), StateFilter(ProductStates))
async def cancel_product_creation(message: Message, state: FSMContext):
    reset_product_data()
    await state.clear()
    await message.answer("Создание продукта отменено. Вы можете начать заново с помощью меню.") 


# Обработчик команды /done
@router.message(Command("done"))
async def finish_product_creation(message: Message, state: FSMContext, api_client):
    """Завершает создание продукта и отправляет данные на сервер"""
    current_state = await state.get_state()
    print(f"Получена команда /done от пользователя {message.from_user.id}, текущее состояние: {current_state}")
    
    if current_state == ProductStates.waiting_for_photo:
        await message.answer("Начинаю отправку данных на сервер...")
        await send_product_to_api(message, state, api_client)
    else:
        await message.answer("Команда /done доступна только при добавлении фотографий продукта.") 