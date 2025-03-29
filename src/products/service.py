from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, func
from sqlalchemy.orm import joinedload
from typing import List, Optional
from .models import Product, Category, ProductCategory
from .schemas import ProductCreate, ProductUpdate, ProductFilter, ProductListResponse
import uuid
from fastapi import HTTPException
from math import ceil
from ..aws import s3_client
from ..settings.config import settings
import re


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    @staticmethod
    def get_full_image_url(relative_path: str) -> str:
        """Преобразует относительный путь в полный URL"""
        # Проверяем, не содержит ли путь уже полный URL
        if relative_path.startswith(('http://', 'https://')):
            # Если путь уже содержит URL, извлекаем только относительный путь
            # Ищем последнее вхождение 'products/'
            match = re.search(r'(.*products/)(products/.+)', relative_path)
            if match:
                relative_path = match.group(2)
            else:
                # Если не удалось найти паттерн, используем последнюю часть пути
                relative_path = relative_path.split('/')[-1]
                relative_path = f"products/{relative_path}"
        
        return f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/{relative_path}"
        
    @staticmethod
    def get_full_image_urls(product: Product) -> None:
        """Преобразует относительные пути в полные URL для продукта"""
        if product.images:
            product.images = [ProductService.get_full_image_url(path) for path in product.images]

    async def create_product(self, product_data: ProductCreate) -> Product:
        """Создает новый продукт"""
        # Проверяем существование категорий
        for category_name in product_data.categories:
            category = await self.session.execute(
                select(Category).where(Category.name == category_name)
            )
            if not category.scalar_one_or_none():
                raise HTTPException(
                    status_code=404,
                    detail=f"Категория '{category_name}' не найдена"
                )

        # Создаем продукт
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            images=product_data.images,
            is_available=True
        )
        self.session.add(product)
        await self.session.flush()

        # Создаем связи с категориями
        for category_name in product_data.categories:
            product_category = ProductCategory(
                product_id=product.id,
                category_name=category_name
            )
            self.session.add(product_category)

        await self.session.commit()
        
        # Получаем продукт с категориями
        result = await self.session.execute(
            select(Product)
            .options(joinedload(Product.categories))
            .where(Product.id == product.id)
        )
        
        # Используем unique() для обработки результатов с коллекциями
        product = result.unique().scalar_one()
        
        # Преобразуем относительные пути в полные URL
        self.get_full_image_urls(product)
        
        return product

    async def update_product(
        self,
        product_id: uuid.UUID,
        product_data: ProductUpdate
    ) -> Product:
        """Обновляет продукт"""
        product = await self.get_product_by_id(product_id)

        # Обновляем базовые поля
        if product_data.name is not None:
            product.name = product_data.name
        if product_data.description is not None:
            product.description = product_data.description
        if product_data.price is not None:
            product.price = product_data.price
        if product_data.is_available is not None:
            product.is_available = product_data.is_available

        # Обновляем изображения если они были переданы
        if product_data.images is not None:
            # Удаляем старые изображения из S3
            if product.images:
                for old_url in product.images:
                    try:
                        object_name = old_url.split('/')[-1]
                        await s3_client.delete_file(f"products/{object_name}")
                    except Exception as e:
                        print(f"Ошибка при удалении изображения {old_url}: {str(e)}")
            
            # Устанавливаем новые изображения
            product.images = product_data.images

        # Обновляем категории если они были переданы
        if product_data.categories is not None:
            # Проверяем существование новых категорий
            for category_name in product_data.categories:
                category = await self.session.execute(
                    select(Category).where(Category.name == category_name)
                )
                if not category.scalar_one_or_none():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Категория '{category_name}' не найдена"
                    )

            # Удаляем старые связи
            await self.session.execute(
                delete(ProductCategory).where(
                    ProductCategory.product_id == product_id
                )
            )

            # Создаем новые связи
            for category_name in product_data.categories:
                product_category = ProductCategory(
                    product_id=product_id,
                    category_name=category_name
                )
                self.session.add(product_category)

        await self.session.commit()
        
        # Получаем продукт с категориями
        result = await self.session.execute(
            select(Product)
            .options(joinedload(Product.categories))
            .where(Product.id == product_id)
        )
        
        # Используем unique() для обработки результатов с коллекциями
        product = result.unique().scalar_one()
        
        # Преобразуем относительные пути в полные URL
        self.get_full_image_urls(product)
        
        return product

    async def delete_product(self, product_id: uuid.UUID) -> None:
        """Удаляет продукт"""
        product = await self.get_product_by_id(product_id)
        
        # Удаляем изображения из S3
        if product.images:
            for url in product.images:
                try:
                    # Получаем относительный путь из полного URL
                    path_parts = url.split(f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/")
                    if len(path_parts) > 1:
                        object_name = path_parts[1]
                        await s3_client.delete_file(object_name)
                except Exception as e:
                    print(f"Ошибка при удалении изображения {url}: {str(e)}")
        
        await self.session.delete(product)
        await self.session.commit()

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product:
        """Получает продукт по ID"""
        result = await self.session.execute(
            select(Product)
            .options(joinedload(Product.categories))
            .where(Product.id == product_id)
        )
        
        # Используем unique() для обработки результатов с коллекциями
        product = result.unique().scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Продукт с ID {product_id} не найден"
            )
        
        # Преобразуем относительные пути в полные URL
        self.get_full_image_urls(product)
        
        return product

    async def get_products(
        self,
        filter_params: ProductFilter,
        page: int = 1,
        size: int = 20
    ) -> ProductListResponse:
        """Получает список продуктов с фильтрацией и пагинацией"""
        query = select(Product).options(joinedload(Product.categories))
        conditions = []

        # Применяем фильтры
        if filter_params.category_name:
            query = query.join(ProductCategory).join(Category)
            conditions.append(Category.name == filter_params.category_name)
        
        if filter_params.min_price is not None:
            conditions.append(Product.price >= filter_params.min_price)
        
        if filter_params.max_price is not None:
            conditions.append(Product.price <= filter_params.max_price)
        
        if filter_params.is_available is not None:
            conditions.append(Product.is_available == filter_params.is_available)
        
        if filter_params.search_query:
            search = f"%{filter_params.search_query}%"
            conditions.append(
                or_(
                    Product.name.ilike(search),
                    Product.description.ilike(search)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Проверяем, запрашиваются ли все продукты (большой размер страницы)
        is_all_products = size >= 1000

        # Получаем общее количество только если нужна пагинация
        total = 0
        if not is_all_products:
            total_query = select(func.count(Product.id)).where(*conditions)
            total_result = await self.session.execute(total_query)
            total = total_result.scalar() or 0

        # Применяем пагинацию только если нужно
        if not is_all_products:
            query = query.offset((page - 1) * size).limit(size)
        
        # Получаем результаты
        result = await self.session.execute(query)
        # Используем unique() для обработки результатов с коллекциями
        items = result.unique().scalars().all()
        
        # Преобразуем относительные пути в полные URL для каждого продукта
        for product in items:
            self.get_full_image_urls(product)

        # Если запрашиваются все продукты, устанавливаем общее количество
        # на основе полученных результатов
        if is_all_products:
            total = len(items)

        return ProductListResponse(
            items=list(items),
            total=total,
            page=page,
            size=size,
            pages=ceil(total / size) if total > 0 else 1
        )
