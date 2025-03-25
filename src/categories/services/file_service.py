from fastapi import HTTPException, UploadFile
from typing import Dict, BinaryIO
from uuid import uuid4
from ...aws import s3_client
import io


class FileService:
    """Сервис для работы с файлами категорий"""
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Генерирует уникальное имя файла"""
        extension = original_filename.split('.')[-1]
        return f"categories/{uuid4()}.{extension}"
    
    @staticmethod
    async def upload_file(file: UploadFile | BinaryIO, filename: str = None) -> Dict[str, str]:
        """Загружает файл в S3 и возвращает его URL"""
        try:
            # Проверяем тип файла
            if isinstance(file, UploadFile):
                content_type = file.content_type
                if not content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=400,
                        detail="Файл должен быть изображением"
                    )
                file_content = await file.read()
                if not filename:
                    filename = FileService.generate_unique_filename(file.filename)
            else:
                content_type = 'image/jpeg'
                file_content = file.read()
                file.seek(0)
                if not filename:
                    filename = FileService.generate_unique_filename("image.jpg")
            
            # Создаем BytesIO объект
            file_io = io.BytesIO(file_content)
            
            # Загружаем файл в S3
            url = await s3_client.upload_file(
                file_io,
                filename,
                content_type=content_type
            )
            
            if not url:
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка при загрузке файла в S3"
                )
            
            return {"url": filename}
            
        except Exception as e:
            print(f"Ошибка при загрузке файла: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при загрузке файла: {str(e)}"
            ) 