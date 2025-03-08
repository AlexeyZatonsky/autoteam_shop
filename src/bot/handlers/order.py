from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from ..states import OrderStates

router = Router(name="order")


@router.callback_query(F.data.startswith("order:"))
async def order_callback_handler(callback: types.CallbackQuery, state: FSMContext, api_client):
    """Обработчик всех callback-запросов для заказов"""
    operation = callback.data.split(":")[1]
    await handle_order_action(callback.message, operation, state, api_client.make_request)
    await callback.answer()


async def handle_order_action(message: types.Message, operation: str, state: FSMContext, make_request):
    """Обработка действий с заказами"""
    if operation == "list":
        await handle_orders_list(message, make_request)
    elif operation == "get_by_id":
        await message.answer("Отправьте ID заказа")
    elif operation == "get_by_user":
        await message.answer("Отправьте ID пользователя")
    elif operation == "change_status":
        await message.answer(
            "Отправьте данные в формате: ID_заказа статус\n"
            "Например: 123 processing"
        )


async def handle_orders_list(message: types.Message, make_request):
    """Обработка запроса списка заказов"""
    try:
        orders = await make_request("GET", "/api/orders/")
        text = "📥 Список заказов:\n\n"
        
        for order in orders:
            text += (f"Заказ #{order['id']}\n"
                    f"Сумма: {order['total_amount']}₽\n"
                    f"Статус: {order['status']}\n\n")
        
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении списка заказов: {str(e)}") 