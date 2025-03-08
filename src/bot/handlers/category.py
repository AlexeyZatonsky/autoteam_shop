from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from ..states import CategoryStates
from ..keyboards import (
    get_category_management_menu,
    get_category_list_keyboard,
    get_category_creation_keyboard,
    get_category_created_keyboard,
    get_category_view_keyboard,
    get_category_delete_confirmation_keyboard
)

router = Router(name="category")


@router.callback_query(F.data.startswith("category:"))
async def category_callback_handler(callback: types.CallbackQuery, state: FSMContext, api_client):
    """Обработчик всех callback-запросов для категорий"""
    operation = callback.data.split(":")[1]
    args = callback.data.split(":")[2:] if len(callback.data.split(":")) > 2 else []
    
    await handle_category_action(callback.message, operation, args, state, api_client.make_request)
    await callback.answer()


@router.message(CategoryStates.waiting_for_name)
async def category_name_handler(message: types.Message, state: FSMContext, api_client):
    """Обработчик ввода имени категории"""
    await process_category_name(message, state, api_client.make_request)


async def handle_category_action(message: types.Message, operation: str, args: list, state: FSMContext, make_request):
    """Обработка действий с категориями"""
    if operation == "manage":
        await message.edit_text(
            "Управление категориями:",
            reply_markup=get_category_management_menu()
        )
        
    elif operation == "list":
        categories = await make_request("GET", "/api/categories")
        text = "📁 Список категорий:\n\n"
        
        for category in categories:
            text += f"• {category['name']}\n"
        
        await message.edit_text(
            text,
            reply_markup=get_category_list_keyboard(categories)
        )
        
    elif operation == "add":
        await state.set_state(CategoryStates.waiting_for_name)
        await message.edit_text(
            "Отправьте название новой категории:",
            reply_markup=get_category_creation_keyboard()
        )
        
    elif operation == "cancel":
        await state.clear()
        await handle_category_action(message, "manage", [], state, make_request)

    elif operation == "view":
        if not args:
            await message.answer("Ошибка: не указано имя категории")
            return
            
        category_name = args[0]
        try:
            category = await make_request("GET", f"/api/categories/{category_name}")
            await message.edit_text(
                f"📁 Категория: {category['name']}",
                reply_markup=get_category_view_keyboard(category_name)
            )
        except Exception as e:
            await message.edit_text(
                f"❌ Ошибка при получении категории: {str(e)}"
            )

    elif operation == "confirm_delete":
        if not args:
            await message.answer("Ошибка: не указано имя категории")
            return
            
        category_name = args[0]
        await state.update_data(category_to_delete=category_name)
        await state.set_state(CategoryStates.waiting_for_delete_confirmation)
        
        await message.edit_text(
            f"❗️ Вы уверены, что хотите удалить категорию '{category_name}'?\n"
            "Это действие нельзя отменить.",
            reply_markup=get_category_delete_confirmation_keyboard(category_name)
        )
        
    elif operation == "delete":
        if not args:
            await message.answer("Ошибка: не указано имя категории")
            return
            
        category_name = args[0]
        try:
            await make_request("DELETE", f"/api/categories/{category_name}")
            await state.clear()
            await message.edit_text(
                f"✅ Категория '{category_name}' успешно удалена!",
                reply_markup=get_category_management_menu()
            )
        except Exception as e:
            await message.edit_text(
                f"❌ Ошибка при удалении категории: {str(e)}"
            )


async def process_category_name(message: types.Message, state: FSMContext, make_request):
    """Обработка ввода названия категории"""
    try:
        category_data = {
            "name": message.text
        }
        await make_request("POST", "/api/categories", json=category_data)
        
        await state.clear()
        
        await message.answer(
            f"✅ Категория '{message.text}' успешно создана!",
            reply_markup=get_category_created_keyboard()
        )
        
    except Exception as e:
        error_msg = str(e)
        if "уже существует" in error_msg:
            await message.answer(
                f"❌ Категория с названием '{message.text}' уже существует.\n"
                "Попробуйте другое название."
            )
        else:
            await message.answer(f"❌ Ошибка при создании категории: {error_msg}") 