from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Category
from .schemas import CategoryCreate, CategoryRead
from fastapi import HTTPException


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_category(self, category_data: CategoryCreate) -> Category:
        """Создание новой категории"""
        # Проверяем, существует ли категория с таким именем
        existing = await self.session.execute(
            select(Category).where(Category.name == category_data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Категория с названием '{category_data.name}' уже существует"
            )

        # Создаем новую категорию
        category = Category(name=category_data.name)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
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
        return category

    async def get_all_categories(self) -> list[Category]:
        """Получение списка всех категорий"""
        result = await self.session.execute(select(Category))
        return list(result.scalars().all())

    async def delete_category(self, name: str) -> None:
        """Удаление категории по имени"""
        category = await self.get_category_by_name(name)
        await self.session.delete(category)
        await self.session.commit()

    async def update_category(self, name: str, new_description: str) -> Category:
        """Обновление описания категории"""
        category = await self.get_category_by_name(name)
        await self.session.commit()
        await self.session.refresh(category)
        return category
