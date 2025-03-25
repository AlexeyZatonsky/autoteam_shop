from fastapi import HTTPException, UploadFile
from typing import Dict, BinaryIO
from uuid import uuid4
from ...aws import s3_client
import io

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp']
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
class FileService:
    """Сервис для работы с файлами категорий"""
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Генерирует уникальное имя файла"""
        extension = original_filename.split('.')[-1]
        return f"categories/{uuid4()}.{extension}"
    
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
            object_name = f"categories/{uuid4()}.{file_ext}"
            
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