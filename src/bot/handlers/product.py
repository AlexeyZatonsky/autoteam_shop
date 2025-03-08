from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from ..states import ProductStates

router = Router(name="product")


@router.callback_query(F.data.startswith("product:"))
async def product_callback_handler(callback: types.CallbackQuery, state: FSMContext, api_client):
    """Обработчик всех callback-запросов для продуктов"""
    operation = callback.data.split(":")[1]
    await handle_product_action(callback.message, operation, state, api_client.make_request)
    await callback.answer()


async def handle_product_action(message: types.Message, operation: str, state: FSMContext, make_request):
    """Обработка действий с продуктами"""
    if operation == "add":
        await message.answer(
            "Отправьте данные продукта в формате: Имя, Описание, Цена, Категория ID"
        )
    elif operation == "delete":
        await message.answer("Отправьте ID продукта для удаления")
    elif operation == "list":
        await handle_products_list(message, make_request)


async def handle_products_list(message: types.Message, make_request):
    """Обработка запроса списка продуктов"""
    try:
        products = await make_request("GET", "/api/products/")
        text = "📦 Список продуктов:\n\n"
        
        for product in products:
            text += f"• {product['name']} - {product['price']}₽\n"
        
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении списка продуктов: {str(e)}") 