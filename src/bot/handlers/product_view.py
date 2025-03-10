from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from ..states.product import ProductStates
from ..keyboards.product import get_product_view_keyboard
from ..api import ProductAPI
from ..services import BotFileService
import re
import io
from src.aws import s3_client

router = Router(name="product_view")


def fix_image_url(url: str) -> str:
    """Исправляет URL изображения, удаляя повторяющиеся префиксы"""
    if not url:
        return url
    
    # Если URL начинается с http:// или https://
    if url.startswith(('http://', 'https://')):
        # Находим последнее вхождение 'products/products/'
        pattern = r'(.*?products/)(products/.+)'
        match = re.search(pattern, url)
        if match:
            # Берем только первую часть URL и последнюю часть пути
            base_url = match.group(1)
            relative_path = match.group(2)
            return f"{base_url}{relative_path}"
        
        # Если не нашли паттерн, но URL содержит несколько http://
        if url.count('http://') > 1 or url.count('https://') > 1:
            # Находим последний http:// или https://
            last_http = url.rfind('http://')
            last_https = url.rfind('https://')
            last_protocol = max(last_http, last_https)
            if last_protocol > 0:
                return url[last_protocol:]
    
    return url


def extract_object_name(url: str) -> str:
    """Извлекает имя объекта из URL изображения для S3"""
    if not url:
        return None
    
    # Если URL содержит 'products/'
    if 'products/' in url:
        # Ищем последнее вхождение 'products/'
        parts = url.split('products/')
        if len(parts) > 1:
            # Берем последнюю часть после 'products/'
            filename = parts[-1]
            # Проверяем, не содержит ли filename еще один путь
            if '/' in filename:
                # Если содержит, берем только имя файла
                filename = filename.split('/')[-1]
            return f"products/{filename}"
    
    return None


@router.callback_query(F.data.startswith("product:view:"))
async def handle_product_view(callback: CallbackQuery, api_client, state: FSMContext):
    """Обрабатывает запрос на просмотр деталей продукта"""
    parts = callback.data.split(":")
    product_id = parts[2]
    
    try:
        # Получаем детали продукта с API
        product = await ProductAPI(api_client).get_product(product_id)
        
        if not product:
            await callback.message.answer(
                "Продукт не найден или был удален.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
                ])
            )
            return
        
        # Исправляем URL изображений
        if product.get('images'):
            product['images'] = [fix_image_url(img) for img in product['images']]
        
        # Формируем текст с деталями продукта
        has_images = product.get('images') and len(product['images']) > 0
        total_images = len(product['images']) if has_images else 0
        
        text = f"📦 *{product['name']}*"
        if has_images:
            text += f" (Фото 1/{total_images})"
        text += "\n\n"
        
        if product.get('description'):
            text += f"📝 *Описание:* {product['description']}\n\n"
        text += f"💰 *Цена:* {product['price']} руб.\n"
        
        # Добавляем категории
        if product.get('categories'):
            categories = [cat['name'] for cat in product['categories']]
            text += f"🏷️ *Категории:* {', '.join(categories)}\n"
        
        # Создаем клавиатуру для просмотра продукта
        keyboard = get_product_view_keyboard(product_id)
        
        # Если есть изображения, отправляем первое изображение с текстом
        if has_images:
            try:
                # Извлекаем относительный путь к изображению из URL
                image_url = product['images'][0]
                object_name = extract_object_name(image_url)
                
                print(f"Извлеченное имя объекта: {object_name}")
                
                if object_name:
                    # Загружаем изображение из S3
                    image_data = await s3_client.get_file(object_name)
                    
                    if image_data:
                        # Создаем BytesIO объект для отправки в Telegram
                        photo = io.BytesIO(image_data)
                        photo.name = object_name.split('/')[-1]
                        
                        try:
                            # Создаем InputFile из BytesIO
                            from aiogram.types import FSInputFile
                            
                            # Сохраняем временный файл
                            temp_filename = f"temp_{photo.name}"
                            with open(temp_filename, "wb") as f:
                                f.write(image_data)
                            
                            # Отправляем фото как FSInputFile
                            await callback.message.answer_photo(
                                photo=FSInputFile(temp_filename),
                                caption=text,
                                reply_markup=keyboard,
                                parse_mode="Markdown"
                            )
                            
                            # Удаляем временный файл
                            import os
                            os.remove(temp_filename)
                        except Exception as e:
                            print(f"Ошибка при отправке фото через FSInputFile: {str(e)}")
                            # Если не удалось отправить фото, отправляем текст
                            await callback.message.answer(
                                text + f"\n\n⚠️ *Не удалось отправить изображение: {str(e)}*",
                                reply_markup=keyboard,
                                parse_mode="Markdown"
                            )
                    else:
                        # Если не удалось загрузить изображение, отправляем текст
                        await callback.message.answer(
                            text + "\n\n⚠️ *Не удалось загрузить изображение из хранилища*",
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                else:
                    # Если не удалось извлечь имя объекта, отправляем текст
                    await callback.message.answer(
                        text + "\n\n⚠️ *Не удалось определить путь к изображению*",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                print(f"Ошибка при отправке фото: {str(e)}")
                # Если не удалось отправить фото, отправляем текст
                await callback.message.answer(
                    text + f"\n\n⚠️ *Не удалось загрузить изображение: {str(e)}*",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        else:
            # Если нет изображений, просто отправляем текст
            await callback.message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Ошибка при получении деталей продукта: {str(e)}")
        await callback.message.answer(
            f"Ошибка при получении деталей продукта: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
            ])
        )


@router.callback_query(F.data.startswith("product:next_image:") | F.data.startswith("product:prev_image:"))
async def handle_product_image_navigation(callback: CallbackQuery, api_client, state: FSMContext):
    """Обрабатывает навигацию по изображениям продукта"""
    parts = callback.data.split(":")
    action = parts[1]
    product_id = parts[2]
    current_index = int(parts[3])
    next_image = action == "next_image"
    
    try:
        # Получаем детали продукта с API
        product = await ProductAPI(api_client).get_product(product_id)
        
        if not product or not product.get('images') or len(product['images']) == 0:
            await callback.message.answer(
                "У этого продукта нет изображений.",
                reply_markup=get_product_view_keyboard(product_id),
                parse_mode="Markdown"
            )
            return
        
        # Исправляем URL изображений
        product['images'] = [fix_image_url(img) for img in product['images']]
        
        # Вычисляем новый индекс изображения
        images = product['images']
        total_images = len(images)
        
        if next_image:
            new_index = (current_index + 1) % total_images
        else:
            new_index = (current_index - 1) % total_images
        
        # Формируем текст с деталями продукта
        text = f"📦 *{product['name']}* (Фото {new_index + 1}/{total_images})\n\n"
        if product.get('description'):
            text += f"📝 *Описание:* {product['description']}\n\n"
        text += f"💰 *Цена:* {product['price']} руб.\n"
        
        # Добавляем категории
        if product.get('categories'):
            categories = [cat['name'] for cat in product['categories']]
            text += f"🏷️ *Категории:* {', '.join(categories)}\n"
        
        # Создаем обновленную клавиатуру с новым индексом
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Пред. фото", 
                        callback_data=f"product:prev_image:{product_id}:{new_index}"
                    ),
                    InlineKeyboardButton(
                        text="След. фото ▶️", 
                        callback_data=f"product:next_image:{product_id}:{new_index}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ Изменить название", 
                        callback_data=f"product:edit_name:{product_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ Изменить описание", 
                        callback_data=f"product:edit_description:{product_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ Изменить цену", 
                        callback_data=f"product:edit_price:{product_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ Изменить категории", 
                        callback_data=f"product:edit_categories:{product_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Удалить", 
                        callback_data=f"product:confirm_delete:{product_id}"
                    )
                ],
                [
                    InlineKeyboardButton(text="🔙 К списку", callback_data="product:list")
                ]
            ]
        )
        
        # Отправляем новое сообщение с фото
        try:
            # Извлекаем относительный путь к изображению из URL
            image_url = images[new_index]
            object_name = extract_object_name(image_url)
            
            print(f"Извлеченное имя объекта: {object_name}")
            
            if object_name:
                # Загружаем изображение из S3
                image_data = await s3_client.get_file(object_name)
                
                if image_data:
                    # Создаем BytesIO объект для отправки в Telegram
                    photo = io.BytesIO(image_data)
                    photo.name = object_name.split('/')[-1]
                    
                    try:
                        # Создаем InputFile из BytesIO
                        from aiogram.types import FSInputFile
                        
                        # Сохраняем временный файл
                        temp_filename = f"temp_{photo.name}"
                        with open(temp_filename, "wb") as f:
                            f.write(image_data)
                        
                        # Отправляем фото как FSInputFile
                        await callback.message.answer_photo(
                            photo=FSInputFile(temp_filename),
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                        
                        # Удаляем временный файл
                        import os
                        os.remove(temp_filename)
                    except Exception as e:
                        print(f"Ошибка при отправке фото через FSInputFile: {str(e)}")
                        # Если не удалось отправить фото, отправляем текст
                        await callback.message.answer(
                            text + f"\n\n⚠️ *Не удалось отправить изображение: {str(e)}*",
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                else:
                    # Если не удалось загрузить изображение, отправляем текст
                    await callback.message.answer(
                        text + "\n\n⚠️ *Не удалось загрузить изображение из хранилища*",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            else:
                # Если не удалось извлечь имя объекта, отправляем текст
                await callback.message.answer(
                    text + "\n\n⚠️ *Не удалось определить путь к изображению*",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Ошибка при отправке фото: {str(e)}")
            # Если не удалось отправить фото, отправляем текст
            await callback.message.answer(
                text + f"\n\n⚠️ *Не удалось загрузить изображение: {str(e)}*",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Ошибка при навигации по изображениям: {str(e)}")
        await callback.message.answer(
            f"Ошибка при навигации по изображениям: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку продуктов", callback_data="product:list")]
            ])
        ) 