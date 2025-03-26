from typing import List, Dict, Optional, Any, BinaryIO
import io
from ..api_client import APIClient


class CategoryAPI:
    """API клиент для работы с категориями"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def get_categories(self) -> List[Dict]:
        """Получает список всех категорий"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="api/categories"
        )
    
    async def get_category(self, name: str) -> Dict:
        """Получает категорию по имени"""
        return await self.api_client.make_request(
            method="GET",
            endpoint=f"api/categories/{name}"
        )
    
    async def create_category(self, name: str, image_url: Optional[str] = None) -> Dict:
        """Создает новую категорию"""
        # Создаем FormData
        data = {
            "name": name
        }
        
        # Если есть URL изображения, добавляем его
        if image_url:
            data["image"] = image_url
            
        return await self.api_client.make_request(
            method="POST",
            endpoint="api/categories",
            data=data,
            is_form_data=True  # Указываем, что данные в формате FormData
        )
    
    async def update_category_name(self, old_name: str, new_name: str) -> Dict:
        """Обновляет имя категории"""
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"api/categories/{old_name}",
            data={"new_name": new_name}
        )
    
    async def update_category_image(self, name: str, image_url: str) -> Dict:
        """Обновляет изображение категории, используя URL изображения"""
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"api/categories/{name}/image",
            data={"image": image_url}
        )
    
    async def update_category_image_with_file(self, name: str, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict:
        """Обновляет изображение категории с загрузкой файла в одном запросе"""
        # Сначала загружаем файл, а затем обновляем категорию
        upload_result = await self.upload_file(file_content, filename, content_type)
        if not upload_result or "url" not in upload_result:
            raise Exception("Не удалось загрузить файл")
            
        return await self.update_category_image(name, upload_result["url"])
    
    async def delete_category(self, name: str) -> Dict:
        """Удаляет категорию"""
        return await self.api_client.make_request(
            method="DELETE",
            endpoint=f"api/categories/{name}"
        )
    
    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict:
        """Загружает файл на сервер и возвращает URL"""
        files = [
            ("file", (filename, file_content, content_type))
        ]
        
        return await self.api_client.make_request(
            method="POST",
            endpoint="api/categories/upload",
            files=files
        ) 