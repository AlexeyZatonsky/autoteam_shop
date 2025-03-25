from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from src.bot.states.category import CategoryStates
from src.bot.keyboards.category import (
    get_category_management_menu,
    get_category_list_keyboard,
    get_category_creation_keyboard,
    get_category_created_keyboard,
    get_category_view_keyboard,
    get_category_delete_confirmation_keyboard,
    get_category_image_view_keyboard
)
import io

router = Router(name="category")


@router.callback_query(F.data.startswith("category:"))
async def category_callback_handler(callback: CallbackQuery, state: FSMContext, api_client):
    """Обработчик всех callback-запросов для категорий"""
    try:
        await callback.answer()
        _, action, *args = callback.data.split(":")
        
        handlers = {
            "manage": handle_manage,
            "list": handle_list,
            "add": handle_add,
            "cancel": handle_cancel,
            "view": handle_view,
            "view_image": handle_view_image,
            "edit_name": handle_edit_name,
            "edit_image": handle_edit_image,
            "confirm_delete": handle_confirm_delete,
            "delete": handle_delete
        }
        
        handler = handlers.get(action)
        if handler:
            await handler(callback.message, args, state, api_client.make_request)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            _, action, *args = callback.data.split(":")
            handler = handlers.get(action)
            if handler:
                await handler(callback.message, args, state, api_client.make_request, new_message=True)
        else:
            raise


@router.message(CategoryStates.waiting_for_name)
async def category_name_handler(message: Message, state: FSMContext, api_client):
    """Обработчик ввода имени категории"""
    try:
        name = message.text.strip()
        
        # Проверяем длину названия
        if len(name) < 2:
            await message.answer(
                "❌ Название категории должно содержать минимум 2 символа.\n"
                "Попробуйте другое название."
            )
            return
            
        if len(name) > 50:
            await message.answer(
                "❌ Название категории не должно превышать 50 символов.\n"
                "Попробуйте другое название."
            )
            return
        
        # Сохраняем имя и просим загрузить изображение
        await state.update_data(category_name=name)
        await state.set_state(CategoryStates.waiting_for_image)
        await message.answer(
            "Отлично! Теперь отправьте изображение для категории:",
            reply_markup=get_category_creation_keyboard()
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(CategoryStates.waiting_for_image, F.photo)
async def category_image_handler(message: Message, state: FSMContext, api_client):
    """Обработчик загрузки изображения категории"""
    try:
        data = await state.get_data()
        name = data['category_name']
        
        # Получаем файл фотографии
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_content = await message.bot.download_file(file.file_path)
        
        # Создаем данные для отправки
        files = {
            'image': ('image.jpg', file_content, 'image/jpeg')
        }
        data = {'name': name}
        
        # Отправляем запрос к API
        result = await api_client.make_request(
            method="POST",
            endpoint="api/categories",
            data=data,
            files=files
        )
        
        await state.clear()
        await message.answer(
            f"✅ Категория '{name}' успешно создана!",
            reply_markup=get_category_created_keyboard()
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании категории: {str(e)}")
        await state.clear()


@router.message(CategoryStates.waiting_for_new_name)
async def category_new_name_handler(message: Message, state: FSMContext, api_client):
    """Обработчик изменения имени категории"""
    try:
        new_name = message.text.strip()
        data = await state.get_data()
        old_name = data['category_name']
        
        # Проверяем длину названия
        if len(new_name) < 2 or len(new_name) > 50:
            await message.answer(
                "❌ Название категории должно содержать от 2 до 50 символов.\n"
                "Попробуйте другое название."
            )
            return
        
        # Отправляем запрос к API
        result = await api_client.make_request(
            method="PATCH",
            endpoint=f"api/categories/{old_name}",
            json={"name": new_name}
        )
        
        await state.clear()
        await message.answer(
            f"✅ Название категории изменено на '{new_name}'!",
            reply_markup=get_category_view_keyboard(new_name)
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при изменении названия: {str(e)}")
        await state.clear()


@router.message(CategoryStates.waiting_for_new_image, F.photo)
async def category_new_image_handler(message: Message, state: FSMContext, api_client):
    """Обработчик изменения изображения категории"""
    try:
        data = await state.get_data()
        category_name = data['category_name']
        
        # Получаем файл фотографии
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_content = await message.bot.download_file(file.file_path)
        
        # Создаем данные для отправки
        files = {
            'image': ('image.jpg', file_content, 'image/jpeg')
        }
        
        # Отправляем запрос к API
        result = await api_client.make_request(
            method="PATCH",
            endpoint=f"api/categories/{category_name}/image",
            files=files
        )
        
        await state.clear()
        await message.answer(
            "✅ Изображение категории успешно обновлено!",
            reply_markup=get_category_view_keyboard(category_name)
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении изображения: {str(e)}")
        await state.clear()


async def handle_view_image(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка просмотра изображения категории"""
    if not args:
        await message.answer("Ошибка: не указано имя категории")
        return
        
    category_name = args[0]
    try:
        category = await make_request("GET", f"api/categories/{category_name}")
        
        if category.get('image'):
            keyboard = get_category_image_view_keyboard(category_name)
            await message.answer_photo(
                photo=category['image'],
                caption=f"🖼 Изображение категории '{category_name}'",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "У этой категории нет изображения.",
                reply_markup=get_category_view_keyboard(category_name)
            )
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении изображения: {str(e)}")


async def handle_edit_name(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка изменения названия категории"""
    if not args:
        await message.answer("Ошибка: не указано имя категории")
        return
        
    category_name = args[0]
    await state.set_state(CategoryStates.waiting_for_new_name)
    await state.update_data(category_name=category_name)
    
    text = "Отправьте новое название для категории:"
    keyboard = get_category_creation_keyboard()
    
    if new_message:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)


async def handle_edit_image(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка изменения изображения категории"""
    if not args:
        await message.answer("Ошибка: не указано имя категории")
        return
        
    category_name = args[0]
    await state.set_state(CategoryStates.waiting_for_new_image)
    await state.update_data(category_name=category_name)
    
    text = "Отправьте новое изображение для категории:"
    keyboard = get_category_creation_keyboard()
    
    if new_message:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)


async def handle_manage(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка команды управления категориями"""
    text = "Управление категориями:"
    keyboard = get_category_management_menu()
    
    if new_message:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)


async def handle_list(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка запроса списка категорий"""
    try:
        categories = await make_request(
            "GET", 
            "api/categories",
            headers={"Accept": "application/json"}
        )
        text = "📁 Список категорий:\n\n"
        text += "\n".join(f"• {category['name']}" for category in categories)
        
        keyboard = get_category_list_keyboard(categories)
        
        if new_message:
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.edit_text(text, reply_markup=keyboard)
            
    except Exception as e:
        error_text = f"❌ Ошибка при получении списка категорий: {str(e)}"
        await message.answer(error_text)


async def handle_add(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка добавления новой категории"""
    await state.set_state(CategoryStates.waiting_for_name)
    text = "Отправьте название новой категории:"
    keyboard = get_category_creation_keyboard()
    
    if new_message:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)


async def handle_cancel(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка отмены действия"""
    await state.clear()
    await handle_manage(message, args, state, make_request)


async def handle_view(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка просмотра категории"""
    if not args:
        await message.answer("Ошибка: не указано имя категории")
        return
        
    category_name = args[0]
    try:
        category = await make_request("GET", f"api/categories/{category_name}")
        keyboard = get_category_view_keyboard(category_name)
        text = f"📁 Категория: {category['name']}"
        
        if new_message:
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.edit_text(text, reply_markup=keyboard)
            
    except Exception as e:
        error_text = f"❌ Ошибка при получении категории: {str(e)}"
        await message.answer(error_text)


async def handle_confirm_delete(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка подтверждения удаления категории"""
    if not args:
        await message.answer("Ошибка: не указано имя категории")
        return
        
    category_name = args[0]
    await state.update_data(category_to_delete=category_name)
    await state.set_state(CategoryStates.waiting_for_delete_confirmation)
    
    text = (f"❗️ Вы уверены, что хотите удалить категорию '{category_name}'?\n"
            "Это действие нельзя отменить.")
    keyboard = get_category_delete_confirmation_keyboard(category_name)
    
    if new_message:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)


async def handle_delete(message: Message, args: list, state: FSMContext, make_request, new_message: bool = False):
    """Обработка удаления категории"""
    if not args:
        await message.answer("Ошибка: не указано имя категории")
        return
        
    category_name = args[0]
    try:
        await make_request("DELETE", f"api/categories/{category_name}")
        await state.clear()
        text = f"✅ Категория '{category_name}' успешно удалена!"
        keyboard = get_category_management_menu()
        
        if new_message:
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.edit_text(text, reply_markup=keyboard)
            
    except Exception as e:
        error_text = f"❌ Ошибка при удалении категории: {str(e)}"
        await message.answer(error_text) 