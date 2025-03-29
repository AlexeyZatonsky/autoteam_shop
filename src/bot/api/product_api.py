from typing import Dict, List, Optional, Any, Union
import aiohttp
from ..api_client import APIClient
import uuid
from src.products.schemas import ProductCreate, ProductUpdate


class ProductAPI:
    """Класс для работы с API продуктов"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def get_products(self, search_query: Optional[str] = None, 
                          category_name: Optional[str] = None,
                          page: int = 1, size: int = 20) -> Dict[str, Any]:
        """Получает список продуктов с возможностью фильтрации"""
        params = {"page": page, "size": size}
        
        if search_query:
            params["search_query"] = search_query
        
        if category_name:
            params["category_name"] = category_name
        
        return await self.api_client.make_request(
            method="GET",
            endpoint="api/products",
            params=params,
            headers={"Accept": "application/json"}
        )
    
    async def get_product(self, product_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Получает детали продукта по ID"""
        return await self.api_client.make_request(
            method="GET",
            endpoint=f"api/products/{product_id}",
            headers={"Accept": "application/json"}
        )
    
    async def create_product(self, product_data: ProductCreate) -> Dict[str, Any]:
        """Создает новый продукт"""
        # Проверяем, что все необходимые данные заполнены
        if not product_data.validate_for_api():
            raise ValueError("Не все обязательные поля заполнены")
        
        # Создаем FormData для отправки
        form = aiohttp.FormData()
        
        # Добавляем основные поля
        form.add_field('name', product_data.name)
        if product_data.description:
            form.add_field('description', product_data.description)
        form.add_field('price', str(product_data.price))
        
        # Добавляем категории
        for category in product_data.categories:
            form.add_field('categories', category)
        
        # Добавляем изображения
        for image_url in product_data.images:
            form.add_field('images', image_url)
        
        return await self.api_client.make_request(
            method="POST",
            endpoint="api/products",
            data=form
        )
    
    async def update_product(self, product_id: Union[str, uuid.UUID], 
                            product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет продукт (частично)"""
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"api/products/{product_id}",
            data=product_data
        )
    
    async def update_product_images(self, product_id: Union[str, uuid.UUID], 
                                  images: List[str]) -> Dict[str, Any]:
        """Обновляет изображения продукта"""
        return await self.api_client.make_request(
            method="PUT",
            endpoint=f"api/products/{product_id}/images",
            data={"images": images}
        )
    
    async def delete_product(self, product_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Удаляет продукт"""
        return await self.api_client.make_request(
            method="DELETE",
            endpoint=f"api/products/{product_id}"
        )
    
    async def upload_file(self, file_content: bytes, filename: str, 
                         content_type: str = 'image/jpeg') -> Dict[str, Any]:
        """Загружает файл на сервер"""
        form = aiohttp.FormData()
        form.add_field(
            'file',
            file_content,
            filename=filename,
            content_type=content_type
        )
        
        return await self.api_client.make_request(
            method="POST",
            endpoint="api/products/upload",
            data=form
        ) 