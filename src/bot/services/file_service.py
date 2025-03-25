from typing import Tuple, BinaryIO, Optional
import io
from aiogram.types import Message, File
from uuid import uuid4
from src.categories.services.file_service import FileService as CategoriesFileService
from src.products.services.file_service import FileService as ProductsFileService


class BotFileService:
    """Сервис для работы с файлами в боте"""
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Генерирует уникальное имя файла"""
        extension = original_filename.split('.')[-1]
        return f"{uuid4()}.{extension}"
    
    @staticmethod
    async def download_photo(message: Message) -> Tuple[Optional[bytes], Optional[str]]:
        """Скачивает фото из сообщения и возвращает его содержимое и имя файла"""
        if not message.photo:
            return None, None
        
        try:
            # Получаем файл фотографии
            photo = message.photo[-1]  # Берем самое большое разрешение
            file = await message.bot.get_file(photo.file_id)
            file_content = await message.bot.download_file(file.file_path)
            
            # Генерируем уникальное имя файла
            unique_filename = BotFileService.generate_unique_filename("image.jpg")
            
            return file_content, unique_filename
        except Exception as e:
            print(f"Ошибка при скачивании фото: {str(e)}")
            return None, None
    
    @staticmethod
    def create_binary_file(content: bytes) -> BinaryIO:
        """Создает BytesIO объект из байтов"""
        file = io.BytesIO(content)
        file.seek(0)
        return file 