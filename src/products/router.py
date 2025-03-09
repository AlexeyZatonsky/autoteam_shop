from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from ..database import get_async_session
from .service import ProductService
from .schemas import ProductCreate, ProductRead, ProductUpdate, ProductFilter, ProductListResponse
from .services.file_service import FileService
import uuid

router = APIRouter(prefix="/api/products", tags=["products"])

# Создаем отдельный роутер для загрузки файлов
upload_router = APIRouter(prefix="/api/upload", tags=["upload"])

@upload_router.post("", response_model=Dict[str, str])
async def upload_file(file: UploadFile = File(...)):
    """
    Загружает файл и возвращает его относительный путь.
    
    - **file**: Файл для загрузки (до 10MB, поддерживаются JPEG, PNG, WebP)
    """
    return await FileService.upload_file(file)


@router.post("", response_model=ProductRead)
async def create_product(
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    categories: List[str] = Form(...),
    images: List[str] = Form(...),
    session: AsyncSession = Depends(get_async_session)
) -> ProductRead:
    """
    Создание нового продукта с загрузкой изображений.
    
    - **name**: Название продукта
    - **description**: Описание продукта (опционально)
    - **price**: Цена продукта
    - **categories**: Список категорий
    - **images**: Список URL изображений (от 1 до 6)
    """
    if not (1 <= len(images) <= 6):
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать от 1 до 6 изображений"
        )

    # Создаем продукт
    product_data = ProductCreate(
        name=name,
        description=description,
        price=price,
        images=images,
        categories=categories
    )

    service = ProductService(session)
    return await service.create_product(product_data)


@router.put("/{product_id}/images", response_model=ProductRead)
async def update_product_images(
    product_id: uuid.UUID,
    images: List[str] = Form(...),
    session: AsyncSession = Depends(get_async_session)
) -> ProductRead:
    """
    Обновление изображений продукта.
    
    - **product_id**: ID продукта
    - **images**: Список URL изображений (от 1 до 6)
    """
    if not (1 <= len(images) <= 6):
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать от 1 до 6 изображений"
        )

    service = ProductService(session)
    
    # Обновляем продукт
    update_data = ProductUpdate(images=images)
    return await service.update_product(product_id, update_data)


@router.delete("/{product_id}")
async def delete_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Удаление продукта.
    
    - **product_id**: ID продукта
    """
    service = ProductService(session)
    
    # Получаем продукт для проверки существования и имени
    product = await service.get_product_by_id(product_id)
    product_name = product.name
    
    # Удаляем продукт
    await service.delete_product(product_id)
    return {"message": f"Продукт '{product_name}' успешно удален"}


@router.get("", response_model=ProductListResponse)
async def get_products(
    filter_params: ProductFilter = Depends(),
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_async_session)
) -> ProductListResponse:
    """
    Получение списка продуктов с фильтрацией и пагинацией.
    
    - **filter_params**: Параметры фильтрации
    - **page**: Номер страницы (начиная с 1)
    - **size**: Размер страницы
    """
    service = ProductService(session)
    return await service.get_products(filter_params, page, size)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
) -> ProductRead:
    """
    Получение продукта по ID.
    
    - **product_id**: ID продукта
    """
    service = ProductService(session)
    return await service.get_product_by_id(product_id)
