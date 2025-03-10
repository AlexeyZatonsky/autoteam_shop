from typing import Tuple, BinaryIO, Optional
import io
from aiogram.types import Message, File
from src.products.services.file_service import FileService as ApiFileService


class BotFileService:
    """Сервис для работы с файлами в боте"""
    
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
            unique_filename = ApiFileService.generate_unique_filename("image.jpg")
            
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