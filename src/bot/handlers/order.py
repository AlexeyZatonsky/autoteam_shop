from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from ..states.order import OrderStates
from ..keyboards.order import (
    get_order_management_menu,
    get_order_list_keyboard,
    get_order_view_keyboard,
    get_order_status_keyboard,
    get_order_cancel_confirmation_keyboard
)

router = Router(name="order")


@router.callback_query(F.data.startswith("order:"))
async def order_callback_handler(callback: CallbackQuery, state: FSMContext, api_client):
    """Обработчик всех callback-запросов для заказов"""
    operation = callback.data.split(":")[1]
    await handle_order_action(callback.message, operation, state, api_client.make_request)
    await callback.answer()


async def handle_order_action(message: Message, operation: str, state: FSMContext, make_request):
    """Обработка действий с заказами"""
    if operation == "list":
        await handle_orders_list(message, make_request)
    elif operation == "get_by_id":
        await message.answer("Отправьте ID заказа")
        await state.set_state(OrderStates.waiting_for_order_id)
    elif operation == "get_by_user":
        await message.answer("Отправьте ID пользователя")
        await state.set_state(OrderStates.waiting_for_user_id)
    elif operation == "change_status":
        await message.answer(
            "Отправьте данные в формате: ID_заказа статус\n"
            "Например: 123 processing"
        )
        await state.set_state(OrderStates.waiting_for_status)


async def handle_orders_list(message: Message, make_request):
    """Обработка запроса списка заказов"""
    try:
        orders = await make_request("GET", "api/orders")
        text = "📥 Список заказов:\n\n"
        
        for order in orders:
            text += (f"Заказ #{order['id']}\n"
                    f"Сумма: {order['total_amount']}₽\n"
                    f"Статус: {order['status']}\n\n")
        
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении списка заказов: {str(e)}") 