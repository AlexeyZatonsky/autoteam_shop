from uuid import uuid4
from typing import List, Tuple, Dict, Optional
from datetime import datetime
import os
import io
from typing import BinaryIO
from fastapi import UploadFile, HTTPException
from ...aws import s3_client

# Константы для валидации файлов
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp']
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']

class FileService:
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Генерирует уникальное имя файла на основе UUID и оригинального расширения"""
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.jpg'  # Для файлов без расширения используем .jpg по умолчанию
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid4())[:8]
        return f"{timestamp}_{unique_id}{ext}"

    @staticmethod
    def prepare_image_data(file_content: bytes, original_filename: str) -> Tuple[bytes, str]:
        """Подготавливает данные изображения для сохранения"""
        new_filename = FileService.generate_unique_filename(original_filename)
        return file_content, new_filename
        
    @staticmethod
    def create_binary_file(content: bytes) -> BinaryIO:
        """Создает BytesIO объект из байтов"""
        file = io.BytesIO(content)
        file.seek(0)
        return file
    
    @staticmethod
    async def validate_image(file_content: bytes, content_type: str) -> bool:
        """Проверяет, является ли файл допустимым изображением"""
        # Проверяем размер файла
        if len(file_content) > MAX_IMAGE_SIZE:
            return False
        
        # Проверяем тип файла
        if content_type not in ALLOWED_MIME_TYPES:
            return False
        
        return True
    
    @staticmethod
    async def upload_file(file: UploadFile) -> Dict[str, str]:
        """Загружает файл и возвращает его относительный путь"""
        try:
            # Получаем содержимое файла
            content = await file.read()
            
            # Проверяем тип файла
            if file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неподдерживаемый тип файла: {file.content_type}. Поддерживаются: {', '.join(ALLOWED_MIME_TYPES)}"
                )
            
            # Проверяем размер файла
            if len(content) > MAX_IMAGE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл слишком большой. Максимальный размер: {MAX_IMAGE_SIZE / 1024 / 1024}MB"
                )
            
            # Получаем расширение файла
            file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
            if file_ext not in ALLOWED_EXTENSIONS:
                file_ext = 'jpg'  # Используем jpg по умолчанию
            
            # Генерируем уникальное имя файла
            object_name = f"products/{uuid4()}.{file_ext}"
            
            # Создаем BytesIO объект
            file_io = io.BytesIO(content)
            
            # Загружаем файл в S3
            full_url = await s3_client.upload_file(file_io, object_name, content_type=file.content_type)
            if not full_url:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка при загрузке файла {file.filename}"
                )
            
            # Возвращаем только относительный путь
            return {"url": object_name}
        except HTTPException:
            raise
        except Exception as e:
            print(f"Ошибка при загрузке файла: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Неожиданная ошибка при загрузке файла: {str(e)}"
            ) 