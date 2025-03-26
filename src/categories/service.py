from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from .models import Category
from .schemas import CategoryCreate
from ..aws import s3_client
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
            return relative_path
            
        # Убираем лишний префикс categories/, если он есть дважды
        if relative_path.startswith('categories/categories/'):
            relative_path = relative_path[11:]  # Убираем первый 'categories/'
            
        # Добавляем префикс categories/, если его нет
        if not relative_path.startswith('categories/'):
            relative_path = f"categories/{relative_path}"
        
        return f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/{relative_path}"

    @staticmethod
    def get_full_image_urls(category: Category) -> None:
        """Преобразует относительный путь в полный URL для категории"""
        if category and category.image:
            category.image = CategoryService.get_full_image_url(category.image)

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

        category = Category(
            name=category_data.name,
            image=category_data.image
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
                await s3_client.delete_file(category.image)
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

    async def update_category_image(self, name: str, image_url: str) -> Category:
        """Обновляет изображение категории"""
        category = await self.get_category_by_name(name)
        
        # Удаляем старое изображение из S3, если оно есть
        if category.image:
            try:
                await s3_client.delete_file(category.image)
            except Exception as e:
                print(f"Ошибка при удалении старого изображения: {e}")

        # Обновляем путь к изображению в БД
        category.image = image_url
        await self.session.commit()
        
        # Преобразуем относительный путь в полный URL
        self.get_full_image_urls(category)
        return category 