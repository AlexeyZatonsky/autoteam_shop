from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query, Path, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from ..database import get_async_session
from .service import CategoryService
from .schemas import CategoryCreate, CategoryRead
from .services.file_service import FileService

router = APIRouter(prefix="/categories", tags=["categories"])

# Создаем отдельный роутер для загрузки файлов
upload_router = APIRouter(prefix="/upload", tags=["upload"])


@upload_router.post("", response_model=Dict[str, str])
async def upload_file(file: UploadFile = File(...)):
    """
    Загружает файл и возвращает его относительный путь.
    
    - **file**: Файл для загрузки (поддерживаются JPEG, PNG, WebP)
    """
    return await FileService.upload_file(file)


@router.post("", response_model=CategoryRead)
async def create_category(
    name: str = Query(..., min_length=2, max_length=100),
    image: UploadFile = None,
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Создание новой категории товаров.
    
    - **name**: Название категории (уникальное)
    - **image**: Изображение категории (опционально)
    """
    # Загружаем изображение, если оно предоставлено
    image_url = None
    if image:
        result = await FileService.upload_file(image)
        image_url = result['url']
    
    # Создаем данные категории
    category_data = CategoryCreate(name=name, image=image_url)
    
    service = CategoryService(session)
    return await service.create_category(category_data)


@router.get("", response_model=List[CategoryRead])
async def get_categories(
    session: AsyncSession = Depends(get_async_session)
) -> List[CategoryRead]:
    """
    Получение списка всех категорий.
    """
    service = CategoryService(session)
    return await service.get_all_categories()


@router.get("/{name}", response_model=CategoryRead)
async def get_category(
    name: str = Path(..., min_length=2, max_length=100),
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Получение информации о категории по её названию.
    """
    service = CategoryService(session)
    return await service.get_category_by_name(name)


@router.delete("/{name}")
async def delete_category(
    name: str = Path(..., min_length=2, max_length=100),
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Удаление категории по названию.
    """
    service = CategoryService(session)
    await service.delete_category(name)
    return {"message": f"Категория '{name}' успешно удалена"}


@router.patch("/{name}")
async def update_category_name(
    name: str = Path(..., min_length=2, max_length=100),
    new_name: str = Query(..., min_length=2, max_length=100),
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Обновление названия категории.
    """
    service = CategoryService(session)
    return await service.update_category_name(name, new_name)


@router.patch("/{name}/image")
async def update_category_image(
    name: str = Path(..., min_length=2, max_length=100),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
) -> CategoryRead:
    """
    Обновление изображения категории.
    """
    # Загружаем новое изображение
    result = await FileService.upload_file(image)
    image_url = result['url']
    
    service = CategoryService(session)
    return await service.update_category_image(name, image_url) 