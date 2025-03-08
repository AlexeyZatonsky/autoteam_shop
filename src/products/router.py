from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database import get_async_session
from .service import CategoryService
from .schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/api", tags=["categories"])


@router.post("/categories", response_model=CategoryRead)
async def create_category(
    category_data: CategoryCreate,
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Создание новой категории товаров.
    
    - **name**: Название категории (уникальное)
    """
    service = CategoryService(session)
    return await service.create_category(category_data)


@router.get("/categories", response_model=List[CategoryRead])
async def get_categories(
    session: AsyncSession = Depends(get_async_session)
) -> List[CategoryRead]:
    """
    Получение списка всех категорий.
    """
    service = CategoryService(session)
    return await service.get_all_categories()


@router.get("/categories/{name}", response_model=CategoryRead)
async def get_category(
    name: str,
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Получение информации о категории по её названию.
    """
    service = CategoryService(session)
    return await service.get_category_by_name(name)


@router.delete("/categories/{name}")
async def delete_category(
    name: str,
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Удаление категории по названию.
    """
    service = CategoryService(session)
    await service.delete_category(name)
    return {"message": f"Категория '{name}' успешно удалена"}


@router.put("/categories/{name}", response_model=CategoryRead)
async def update_category(
    name: str,
    new_description: str,
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Обновление описания категории.
    """
    service = CategoryService(session)
    return await service.update_category(name, new_description)
