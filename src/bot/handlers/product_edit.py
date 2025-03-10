from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from ..states.product import ProductStates
from ..api import ProductAPI, CategoryAPI
from ..services import BotFileService
from ..keyboards.product import get_product_delete_confirmation_keyboard

router = Router(name="product_edit")


@router.callback_query(F.data.startswith("product:edit_name:"))
async def start_edit_name(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование названия продукта"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    await state.set_state(ProductStates.editing_name)
    await state.update_data(edit_product_id=product_id)
    await callback.message.answer("Введите новое название продукта (от 2 до 100 символов):")
    await callback.answer()


@router.message(StateFilter(ProductStates.editing_name))
async def process_edit_name(message: Message, state: FSMContext, api_client):
    """Обрабатывает редактирование названия продукта"""
    try:
        # Получаем ID продукта из состояния
        data = await state.get_data()
        product_id = data.get('edit_product_id')
        
        if not product_id:
            await message.answer("Ошибка: ID продукта не найден. Пожалуйста, попробуйте снова.")
            await state.clear()
            return
        
        # Проверяем название
        name = message.text.strip()
        if len(name) < 2:
            await message.answer("Название продукта должно содержать минимум 2 символа. Пожалуйста, попробуйте снова.")
            return
        if len(name) > 100:
            await message.answer("Название продукта не должно превышать 100 символов. Пожалуйста, попробуйте снова.")
            return
        
        # Отправляем запрос на обновление продукта
        response = await ProductAPI(api_client).update_product(
            product_id=product_id,
            product_data={"name": name}
        )
        
        if response:
            await message.answer(f"Название продукта успешно обновлено на '{name}'.")
            # Показываем обновленный продукт
            callback = types.CallbackQuery(
                id="0",
                from_user=message.from_user,
                chat_instance="0",
                message=message,
                data=f"product:view:{product_id}"
            )
            from .product_view import handle_product_view
            await handle_product_view(callback, api_client, state)
        else:
            await message.answer("Ошибка при обновлении названия продукта. Пожалуйста, попробуйте снова.")
        
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        print(f"Ошибка при редактировании названия продукта: {str(e)}")
        await message.answer(f"Произошла ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("product:edit_description:"))
async def start_edit_description(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование описания продукта"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    await state.set_state(ProductStates.editing_description)
    await state.update_data(edit_product_id=product_id)
    await callback.message.answer("Введите новое описание продукта (до 1000 символов):")
    await callback.answer()


@router.message(StateFilter(ProductStates.editing_description))
async def process_edit_description(message: Message, state: FSMContext, api_client):
    """Обрабатывает редактирование описания продукта"""
    try:
        # Получаем ID продукта из состояния
        data = await state.get_data()
        product_id = data.get('edit_product_id')
        
        if not product_id:
            await message.answer("Ошибка: ID продукта не найден. Пожалуйста, попробуйте снова.")
            await state.clear()
            return
        
        # Проверяем описание
        description = message.text.strip()
        if len(description) > 1000:
            await message.answer("Описание продукта не должно превышать 1000 символов. Пожалуйста, попробуйте снова.")
            return
        
        # Отправляем запрос на обновление продукта
        response = await ProductAPI(api_client).update_product(
            product_id=product_id,
            product_data={"description": description}
        )
        
        if response:
            await message.answer("Описание продукта успешно обновлено.")
            # Показываем обновленный продукт
            callback = types.CallbackQuery(
                id="0",
                from_user=message.from_user,
                chat_instance="0",
                message=message,
                data=f"product:view:{product_id}"
            )
            from .product_view import handle_product_view
            await handle_product_view(callback, api_client, state)
        else:
            await message.answer("Ошибка при обновлении описания продукта. Пожалуйста, попробуйте снова.")
        
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        print(f"Ошибка при редактировании описания продукта: {str(e)}")
        await message.answer(f"Произошла ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("product:edit_price:"))
async def start_edit_price(callback: CallbackQuery, state: FSMContext):
    """Начинает редактирование цены продукта"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    await state.set_state(ProductStates.editing_price)
    await state.update_data(edit_product_id=product_id)
    await callback.message.answer("Введите новую цену продукта (число с плавающей точкой, например 1234.56):")
    await callback.answer()


@router.message(StateFilter(ProductStates.editing_price))
async def process_edit_price(message: Message, state: FSMContext, api_client):
    """Обрабатывает редактирование цены продукта"""
    try:
        # Получаем ID продукта из состояния
        data = await state.get_data()
        product_id = data.get('edit_product_id')
        
        if not product_id:
            await message.answer("Ошибка: ID продукта не найден. Пожалуйста, попробуйте снова.")
            await state.clear()
            return
        
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
        
        # Отправляем запрос на обновление продукта
        response = await ProductAPI(api_client).update_product(
            product_id=product_id,
            product_data={"price": price}
        )
        
        if response:
            await message.answer(f"Цена продукта успешно обновлена на {price} руб.")
            # Показываем обновленный продукт
            callback = types.CallbackQuery(
                id="0",
                from_user=message.from_user,
                chat_instance="0",
                message=message,
                data=f"product:view:{product_id}"
            )
            from .product_view import handle_product_view
            await handle_product_view(callback, api_client, state)
        else:
            await message.answer("Ошибка при обновлении цены продукта. Пожалуйста, попробуйте снова.")
        
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        print(f"Ошибка при редактировании цены: {str(e)}")
        await message.answer(f"Произошла ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("product:edit_categories:"))
async def start_edit_categories(callback: CallbackQuery, state: FSMContext, api_client):
    """Начинает редактирование категорий продукта"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    await state.set_state(ProductStates.editing_categories)
    await state.update_data(edit_product_id=product_id)
    
    # Получаем список категорий
    categories = await CategoryAPI(api_client).get_categories()
    
    if not categories:
        await callback.message.answer("Не удалось загрузить список категорий.")
        await state.clear()
        return
    
    # Получаем текущий продукт для отображения выбранных категорий
    product = await ProductAPI(api_client).get_product(product_id)
    
    current_categories = []
    if product and product.get('categories'):
        current_categories = [cat['name'] for cat in product['categories']]
        # Сохраняем текущие категории в состоянии
        await state.update_data(selected_categories=current_categories)
    
    # Создаем клавиатуру с категориями
    keyboard = []
    for i, category in enumerate(categories):
        # Добавляем отметку для выбранных категорий
        mark = "✅ " if category['name'] in current_categories else ""
        # Сохраняем соответствие индекса и имени категории в состоянии
        await state.update_data({f"cat_{i}": category['name']})
        keyboard.append([
            InlineKeyboardButton(
                text=f"{mark}{category['name']}", 
                callback_data=f"cat:{i}"  # Используем короткий идентификатор
            )
        ])
    
    # Добавляем кнопку для завершения выбора
    keyboard.append([
        InlineKeyboardButton(
            text="✅ Завершить выбор", 
            callback_data="cat:done"  # Используем короткий идентификатор
        )
    ])
    
    await callback.message.answer(
        f"Выбранные категории: {', '.join(current_categories) if current_categories else 'нет'}\n\n"
        "Выберите категории для продукта (нажмите на категорию для выбора/отмены):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext, api_client):
    """Обрабатывает выбор категорий при редактировании продукта"""
    parts = callback.data.split(":")
    action = parts[1]
    
    # Получаем текущие данные из состояния
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    selected_categories = data.get('selected_categories', [])
    
    if not product_id:
        await callback.message.answer("Ошибка: ID продукта не найден.")
        await state.clear()
        return
    
    if action == "done":
        # Завершаем выбор категорий
        if not selected_categories:
            await callback.message.answer("Необходимо выбрать хотя бы одну категорию.")
            return
        
        try:
            # Отправляем запрос на обновление категорий продукта
            response = await ProductAPI(api_client).update_product(
                product_id=product_id,
                product_data={"categories": selected_categories}
            )
            
            if response:
                await callback.message.answer(
                    f"Категории продукта успешно обновлены: {', '.join(selected_categories)}",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 К продукту", callback_data=f"product:view:{product_id}")]
                    ])
                )
            else:
                await callback.message.answer(
                    "Ошибка при обновлении категорий продукта.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 К продукту", callback_data=f"product:view:{product_id}")]
                    ])
                )
        except Exception as e:
            await callback.message.answer(
                f"Ошибка при обновлении категорий: {str(e)}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К продукту", callback_data=f"product:view:{product_id}")]
                ])
            )
        
        # Очищаем состояние
        await state.clear()
    else:
        try:
            # Получаем индекс категории
            cat_index = int(action)
            # Получаем имя категории из состояния
            category_name = data.get(f"cat_{cat_index}")
            
            if not category_name:
                await callback.answer("Ошибка: категория не найдена.")
                return
            
            # Если категория уже выбрана, удаляем ее, иначе добавляем
            if category_name in selected_categories:
                selected_categories.remove(category_name)
            else:
                selected_categories.append(category_name)
            
            # Обновляем состояние
            await state.update_data(selected_categories=selected_categories)
            
            # Получаем список всех категорий
            categories = await CategoryAPI(api_client).get_categories()
            
            if not categories:
                await callback.message.answer("Не удалось загрузить список категорий.")
                return
            
            # Создаем обновленную клавиатуру
            keyboard = []
            for i, category in enumerate(categories):
                # Добавляем отметку для выбранных категорий
                mark = "✅ " if category['name'] in selected_categories else ""
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{mark}{category['name']}", 
                        callback_data=f"cat:{i}"
                    )
                ])
            
            # Добавляем кнопку для завершения выбора
            keyboard.append([
                InlineKeyboardButton(
                    text="✅ Завершить выбор", 
                    callback_data="cat:done"
                )
            ])
            
            # Обновляем сообщение
            await callback.message.edit_text(
                f"Выбранные категории: {', '.join(selected_categories) if selected_categories else 'нет'}\n\n"
                "Выберите категории для продукта (нажмите на категорию для выбора/отмены):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        except (ValueError, KeyError) as e:
            print(f"Ошибка при обработке выбора категории: {str(e)}")
            await callback.answer("Произошла ошибка при обработке выбора категории.")
    
    await callback.answer()


@router.callback_query(F.data.startswith("product:confirm_delete:"))
async def confirm_delete_product(callback: CallbackQuery):
    """Показывает подтверждение удаления продукта"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    # Создаем клавиатуру для подтверждения удаления
    keyboard = get_product_delete_confirmation_keyboard(product_id)
    
    await callback.message.answer(
        "⚠️ Вы уверены, что хотите удалить этот продукт? Это действие нельзя отменить.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:delete:"))
async def delete_product(callback: CallbackQuery, api_client):
    """Удаляет продукт"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    try:
        # Отправляем запрос на удаление продукта
        response = await ProductAPI(api_client).delete_product(product_id)
        
        if response:
            await callback.message.answer(
                "✅ Продукт успешно удален!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
                ])
            )
        else:
            await callback.message.answer(
                "❌ Ошибка при удалении продукта. Пожалуйста, попробуйте снова.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
                ])
            )
    except Exception as e:
        print(f"Ошибка при удалении продукта: {str(e)}")
        await callback.message.answer(
            f"❌ Произошла ошибка при удалении продукта: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
            ])
        )
    
    await callback.answer() 