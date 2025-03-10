from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from ..states.product import ProductStates
from ..keyboards.product import get_product_creation_keyboard, get_product_created_keyboard
from src.products.schemas import ProductCreate
from ..api import ProductAPI, CategoryAPI
from ..services import BotFileService
import aiohttp

router = Router(name="product_create")

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


@router.callback_query(F.data == "product:create")
async def start_product_creation(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс создания продукта"""
    reset_product_data()
    await state.set_state(ProductStates.waiting_for_name)
    await callback.message.answer("Введите название продукта (от 2 до 100 символов):")
    await callback.answer()


@router.message(StateFilter(ProductStates.waiting_for_name))
async def process_product_name(message: Message, state: FSMContext):
    """Обрабатывает ввод названия продукта"""
    product_data = get_product_data()
    
    # Проверяем название
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Название продукта должно содержать минимум 2 символа. Пожалуйста, попробуйте снова.")
        return
    if len(name) > 100:
        await message.answer("Название продукта не должно превышать 100 символов. Пожалуйста, попробуйте снова.")
        return
    
    # Сохраняем название
    product_data.name = name
    
    # Переходим к вводу описания
    await state.set_state(ProductStates.waiting_for_description)
    await message.answer(
        "Введите описание продукта (до 1000 символов) или нажмите /skip, чтобы пропустить этот шаг:"
    )


@router.message(Command("skip"), StateFilter(ProductStates.waiting_for_description))
async def skip_product_description(message: Message, state: FSMContext, api_client):
    """Пропускает ввод описания продукта"""
    # Переходим к выбору категории
    categories = await CategoryAPI(api_client).get_categories()
    
    if not categories:
        await message.answer("Не удалось загрузить список категорий. Пожалуйста, попробуйте позже.")
        await state.clear()
        return
    
    # Создаем клавиатуру с категориями
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category['name'], 
                callback_data=f"product_category:{category['name']}"
            )
        ])
    
    await state.set_state(ProductStates.waiting_for_category)
    await message.answer(
        "Выберите категорию для продукта:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.message(StateFilter(ProductStates.waiting_for_description))
async def process_product_description(message: Message, state: FSMContext, api_client):
    """Обрабатывает ввод описания продукта"""
    product_data = get_product_data()
    
    # Проверяем описание
    description = message.text.strip()
    if len(description) > 1000:
        await message.answer("Описание продукта не должно превышать 1000 символов. Пожалуйста, попробуйте снова.")
        return
    
    # Сохраняем описание
    product_data.description = description
    
    # Переходим к выбору категории
    await skip_product_description(message, state, api_client)


@router.callback_query(F.data.startswith("product_category:"), StateFilter(ProductStates.waiting_for_category))
async def process_product_category(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор категории продукта"""
    parts = callback.data.split(":")
    category_name = parts[1]
    
    print(f"Выбрана категория: {category_name}")
    
    product_data = get_product_data()
    
    # Добавляем категорию
    product_data.categories = [category_name]
    
    # Переходим к вводу цены
    await state.set_state(ProductStates.waiting_for_price)
    await callback.message.answer("Категория выбрана: " + category_name)
    await callback.message.answer("Теперь введите цену продукта (число с плавающей точкой, например 1234.56):")
    await callback.answer()


@router.message(StateFilter(ProductStates.waiting_for_price))
async def process_product_price(message: Message, state: FSMContext):
    """Обрабатывает ввод цены продукта"""
    product_data = get_product_data()
    
    # Проверяем цену
    try:
        price_text = message.text.strip().replace(',', '.')
        price = float(price_text)
        if price <= 0:
            raise ValueError("Цена должна быть больше 0")
        if price > 999999.99:
            raise ValueError("Цена не должна превышать 999999.99")
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Пожалуйста, введите корректную цену.")
        return
    
    # Сохраняем цену
    product_data.price = price
    
    # Переходим к загрузке фото
    await state.set_state(ProductStates.waiting_for_photo)
    await message.answer(
        "Отправьте фотографии продукта (до 6 штук). "
        "После загрузки всех фотографий нажмите /done для завершения."
    )


@router.message(StateFilter(ProductStates.waiting_for_photo), ~Command("done"), ~Command("cancel"))
async def process_product_photo(message: Message, state: FSMContext, api_client):
    """Обрабатывает загрузку фотографий продукта"""
    product_data = get_product_data()
    
    # Проверяем, что сообщение содержит фото
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фотографию продукта или нажмите /done для завершения.")
        return
    
    # Проверяем, что не превышен лимит фотографий
    if len(product_data.images) >= 6:
        await message.answer("Вы уже загрузили максимальное количество фотографий (6). Нажмите /done для завершения.")
        return
    
    try:
        # Скачиваем фото
        file_content, unique_filename = await BotFileService.download_photo(message)
        if not file_content or not unique_filename:
            await message.answer("Ошибка при загрузке фото. Пожалуйста, попробуйте еще раз.")
            return
        
        # Загружаем файл на сервер
        response = await ProductAPI(api_client).upload_file(
            file_content=file_content,
            filename=unique_filename,
            content_type='image/jpeg'
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


@router.message(Command("done"), StateFilter(ProductStates.waiting_for_photo))
async def finish_product_creation(message: Message, state: FSMContext, api_client):
    """Завершает создание продукта"""
    product_data = get_product_data()
    
    # Проверяем, что все необходимые данные заполнены
    if not product_data.validate_for_api():
        missing = []
        if not product_data.name or len(product_data.name) < 2:
            missing.append("название")
        if not product_data.price or product_data.price <= 0:
            missing.append("цена")
        if not product_data.categories:
            missing.append("категория")
        if not product_data.images:
            missing.append("фотографии")
        
        await message.answer(
            f"Не все обязательные поля заполнены. Пожалуйста, заполните: {', '.join(missing)}."
        )
        return
    
    try:
        # Отправляем данные на сервер
        response = await ProductAPI(api_client).create_product(product_data)
        
        if response and 'id' in response:
            # Отправляем сообщение об успешном создании
            await message.answer(
                f"Продукт '{product_data.name}' успешно создан!",
                reply_markup=get_product_created_keyboard()
            )
            
            # Сбрасываем данные и состояние
            reset_product_data()
            await state.clear()
        else:
            await message.answer("Ошибка при создании продукта. Пожалуйста, попробуйте снова.")
    except Exception as e:
        print(f"Ошибка при создании продукта: {str(e)}")
        await message.answer(f"Произошла ошибка при создании продукта: {str(e)}")


@router.message(Command("cancel"), StateFilter(ProductStates))
async def cancel_product_creation(message: Message, state: FSMContext):
    """Отменяет создание продукта"""
    reset_product_data()
    await state.clear()
    await message.answer(
        "Создание продукта отменено.",
        reply_markup=get_product_creation_keyboard()
    ) 