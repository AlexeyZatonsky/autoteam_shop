from typing import Dict, List, Any
from ..api_client import APIClient


class CategoryAPI:
    """Класс для работы с API категорий"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Получает список всех категорий"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="api/categories",
            headers={"Accept": "application/json"}
        )
    
    async def get_category(self, category_name: str) -> Dict[str, Any]:
        """Получает детали категории по имени"""
        return await self.api_client.make_request(
            method="GET",
            endpoint=f"api/categories/{category_name}",
            headers={"Accept": "application/json"}
        )
    
    async def create_category(self, name: str, description: str = None) -> Dict[str, Any]:
        """Создает новую категорию"""
        data = {"name": name}
        if description:
            data["description"] = description
            
        return await self.api_client.make_request(
            method="POST",
            endpoint="api/categories",
            data=data
        )
    
    async def update_category(self, name: str, description: str) -> Dict[str, Any]:
        """Обновляет описание категории"""
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"api/categories/{name}",
            data={"description": description}
        )
    
    async def delete_category(self, name: str) -> Dict[str, Any]:
        """Удаляет категорию"""
        return await self.api_client.make_request(
            method="DELETE",
            endpoint=f"api/categories/{name}"
        ) 