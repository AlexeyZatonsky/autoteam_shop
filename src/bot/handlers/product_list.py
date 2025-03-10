from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from ..states.product import ProductStates
from ..keyboards.product import get_product_list_keyboard, get_product_creation_keyboard
from ..api import ProductAPI

router = Router(name="product_list")


@router.callback_query(F.data == "product:list")
async def handle_products_list(callback: CallbackQuery, api_client):
    """Обрабатывает запрос на просмотр списка продуктов"""
    try:
        # Получаем список продуктов с API
        products = await ProductAPI(api_client).get_products()
        
        if not products or not products.get('items') or len(products['items']) == 0:
            # Если продуктов нет, предлагаем создать новый
            await callback.message.answer(
                "Продукты не найдены. Вы можете создать новый продукт.",
                reply_markup=get_product_creation_keyboard()
            )
        else:
            # Отображаем список продуктов
            await callback.message.answer(
                f"Найдено продуктов: {products['total']}",
                reply_markup=get_product_list_keyboard(products['items'])
            )
    except Exception as e:
        print(f"Ошибка при получении списка продуктов: {str(e)}")
        await callback.message.answer(
            f"Ошибка при получении списка продуктов: {str(e)}",
            reply_markup=get_product_creation_keyboard()
        )
    
    await callback.answer()


@router.message(Command("find_product"))
async def find_product_command(message: Message, state: FSMContext):
    """Обрабатывает команду поиска продукта"""
    await state.set_state(ProductStates.waiting_for_search)
    await message.answer(
        "Введите название продукта или его ID для поиска:"
    )


@router.message(StateFilter(ProductStates.waiting_for_search))
async def process_product_search(message: Message, state: FSMContext, api_client):
    """Обрабатывает поиск продукта по названию или ID"""
    search_query = message.text.strip()
    
    if not search_query:
        await message.answer("Пожалуйста, введите название продукта или его ID.")
        return
    
    try:
        # Пробуем найти продукт по ID
        try:
            # Проверяем, является ли запрос UUID
            import uuid
            product_id = uuid.UUID(search_query)
            
            # Получаем продукт по ID
            product = await ProductAPI(api_client).get_product(product_id)
            
            if product:
                # Создаем callback для просмотра продукта
                callback = types.CallbackQuery(
                    id="0",
                    from_user=message.from_user,
                    chat_instance="0",
                    message=message,
                    data=f"product:view:{product_id}"
                )
                from .product_view import handle_product_view
                await handle_product_view(callback, api_client, state)
                await state.clear()
                return
        except (ValueError, uuid.UUID.error, AttributeError):
            # Если не UUID, ищем по названию
            pass
        
        # Ищем продукты по названию
        products = await ProductAPI(api_client).get_products(search_query=search_query)
        
        if products and products.get('items') and len(products['items']) > 0:
            # Создаем клавиатуру с найденными продуктами
            keyboard = []
            for product in products['items']:
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{product['name']} - {product['price']} руб.", 
                        callback_data=f"product:view:{product['id']}"
                    )
                ])
            
            # Добавляем кнопку возврата к списку
            keyboard.append([
                InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")
            ])
            
            await message.answer(
                f"Найдено продуктов: {len(products['items'])}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            await message.answer(
                "Продукты не найдены. Попробуйте другой запрос.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
                ])
            )
    except Exception as e:
        print(f"Ошибка при поиске продукта: {str(e)}")
        await message.answer(
            f"Ошибка при поиске продукта: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
            ])
        )
    
    # Очищаем состояние
    await state.clear() 