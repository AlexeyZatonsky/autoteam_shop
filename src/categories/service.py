from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import Category
from .schemas import CategoryCreate
from ..aws import s3_client
import io
from uuid import uuid4
from fastapi import UploadFile
from ..settings.config import settings
import re


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def get_full_image_url(relative_path: str) -> str:
        """Преобразует относительный путь в полный URL"""
        if not relative_path:
            return None
            
        if relative_path.startswith(('http://', 'https://')):
            # Если путь уже содержит URL, извлекаем только относительный путь
            match = re.search(r'(.*categories/)(categories/.+)', relative_path)
            if match:
                relative_path = match.group(2)
            else:
                relative_path = relative_path.split('/')[-1]
                relative_path = f"categories/{relative_path}"
        
        return f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/{relative_path}"

    @staticmethod
    def get_full_image_urls(category: Category) -> None:
        """Преобразует относительный путь в полный URL для категории"""
        if category.image:
            category.image = CategoryService.get_full_image_url(category.image)

    async def upload_category_image(self, file: UploadFile) -> str:
        """Загружает изображение категории в S3"""
        if not file:
            return None
            
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Файл должен быть изображением"
            )
            
        # Генерируем уникальное имя файла
        file_ext = file.filename.split('.')[-1]
        object_name = f"categories/{uuid4()}.{file_ext}"
        
        file_content = await file.read()
        file_io = io.BytesIO(file_content)
        
        # Загружаем файл в S3
        await s3_client.upload_file(
            file_io, 
            object_name,
            content_type=file.content_type
        )
        
        return object_name

    async def create_category(self, category_data: CategoryCreate) -> Category:
        """Создает новую категорию"""
        # Проверяем, не существует ли уже категория с таким именем
        existing = await self.session.execute(
            select(Category).where(Category.name == category_data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Категория с названием '{category_data.name}' уже существует"
            )
            
        image_url = None
        if category_data.image:
            image_url = await self.upload_category_image(category_data.image)

        category = Category(
            name=category_data.name,
            image=image_url
        )
        self.session.add(category)
        await self.session.commit()
        
        # Преобразуем относительный путь в полный URL
        self.get_full_image_urls(category)
        return category

    async def get_category_by_name(self, name: str) -> Category:
        """Получение категории по имени"""
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Категория '{name}' не найдена"
            )
        
        # Преобразуем относительный путь в полный URL
        self.get_full_image_urls(category)
        return category

    async def get_all_categories(self) -> list[Category]:
        """Получение списка всех категорий"""
        result = await self.session.execute(select(Category))
        categories = list(result.scalars().all())
        
        # Преобразуем относительные пути в полные URL для всех категорий
        for category in categories:
            self.get_full_image_urls(category)
        return categories

    async def delete_category(self, name: str) -> None:
        """Удаление категории по имени"""
        category = await self.get_category_by_name(name)
        
        # Удаляем изображение из S3, если оно есть
        if category.image:
            try:
                path_parts = category.image.split(f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/")
                if len(path_parts) > 1:
                    object_name = path_parts[1]
                    await s3_client.delete_file(object_name)
            except Exception as e:
                print(f"Ошибка при удалении изображения {category.image}: {str(e)}")
        
        await self.session.delete(category)
        await self.session.commit()

    async def update_category_name(self, old_name: str, new_name: str) -> Category:
        """Обновляет название категории"""
        # Проверяем существование категории со старым именем
        category = await self.get_category_by_name(old_name)
        
        # Проверяем, не занято ли новое имя
        if old_name != new_name:
            existing = await self.session.execute(
                select(Category).where(Category.name == new_name)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Категория с названием '{new_name}' уже существует"
                )
        
        # Обновляем имя
        category.name = new_name
        await self.session.commit()
        
        # Преобразуем относительный путь в полный URL
        self.get_full_image_urls(category)
        return category

    async def update_category_image(self, name: str, image: UploadFile) -> Category:
        """Обновляет изображение категории"""
        category = await self.get_category_by_name(name)
        
        # Удаляем старое изображение, если оно есть
        if category.image:
            try:
                path_parts = category.image.split(f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/")
                if len(path_parts) > 1:
                    object_name = path_parts[1]
                    await s3_client.delete_file(object_name)
            except Exception as e:
                print(f"Ошибка при удалении старого изображения: {e}")

        # Загружаем новое изображение
        image_url = await self.upload_category_image(image)
        category.image = image_url
        await self.session.commit()
        
        # Преобразуем относительный путь в полный URL
        self.get_full_image_urls(category)
        return category 