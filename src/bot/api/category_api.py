from typing import List, Dict, Optional, Any, BinaryIO
import io
from ..api_client import APIClient
import aiohttp
from ...settings.config import settings
import asyncio


class CategoryAPI:
    """API клиент для работы с категориями"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    @staticmethod
    def get_image_url(category: Dict) -> Optional[str]:
        """Получает полный URL изображения категории для отображения в Telegram"""
        if not category or 'image' not in category or not category['image']:
            return None
            
        image_url = category['image']
        # Проверяем, является ли URL уже полным
        if not image_url.startswith(('http://', 'https://')):
            # Формируем полный URL используя настройки S3
            return f"{settings.S3_URL}/{settings.S3_BUCKET_NAME}/{image_url}"
            
        return image_url

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
        data = aiohttp.FormData()
        data.add_field("name", name)
        
        # Если есть URL изображения, добавляем его как строку
        if image_url:
            data.add_field("image", image_url)
            
        return await self.api_client.make_request(
            method="POST",
            endpoint="api/categories",
            data=data
        )
    
    async def update_category_name(self, old_name: str, new_name: str) -> Dict:
        """Обновляет имя категории"""
        # Отправляем new_name как query-параметр, а не в теле запроса
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"api/categories/{old_name}?new_name={new_name}"
        )
    
    async def update_category_image(self, name: str, image_url: str) -> Dict:
        """Обновляет изображение категории, используя URL изображения"""
        # Отправляем image_url как параметр формы
        form_data = aiohttp.FormData()
        form_data.add_field('image', image_url)
        
        try:
            url = f"{self.api_client.api_url}api/categories/{name}/image"
            print(f"Отправляем запрос PATCH на {url} с image={image_url}")
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.patch(url, data=form_data) as response:
                    response_text = await response.text()
                    print(f"Ответ сервера: {response.status} - {response_text}")
                    
                    if response.status >= 400:
                        raise Exception(f"API error {response.status}: {response_text}")
                    
                    return await response.json()
        except Exception as e:
            print(f"Ошибка при обновлении изображения: {str(e)}")
            raise Exception(f"Ошибка при обновлении изображения: {str(e)}")
    
    async def update_category_image_with_file(self, name: str, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict:
        """Обновляет изображение категории с загрузкой файла в одном запросе"""
        # Сначала загружаем файл, а затем обновляем категорию
        upload_result = await self.upload_file(file_content, filename, content_type)
        if not upload_result or "url" not in upload_result:
            raise Exception("Не удалось загрузить файл")
            
        # Используем обновленный метод для обновления категории
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

    @staticmethod
    async def download_image_from_url(url: str) -> Optional[bytes]:
        """Скачивает изображение по URL и возвращает его содержимое в виде байтов"""
        if not url:
            print("URL изображения не указан")
            return None
            
        try:
            print(f"Скачиваем изображение по URL: {url}")
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                try:
                    async with session.get(url, timeout=30) as response:
                        print(f"Ответ от сервера: {response.status} {response.reason}")
                        
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            print(f"Тип контента: {content_type}")
                            
                            if 'image' in content_type:
                                content = await response.read()
                                print(f"Получено изображение размером {len(content)} байт")
                                return content
                            else:
                                text = await response.text()
                                print(f"Ошибка: сервер вернул не изображение, а: {text[:200]}")
                                return None
                        else:
                            try:
                                error_text = await response.text()
                                print(f"Ошибка: сервер вернул статус {response.status}: {error_text[:200]}")
                            except:
                                print(f"Ошибка при получении текста ошибки")
                            return None
                except aiohttp.ClientConnectorError as e:
                    print(f"Ошибка соединения с сервером: {str(e)}")
                    return None
                except aiohttp.ClientError as e:
                    print(f"Ошибка клиента при скачивании изображения: {str(e)}")
                    return None
                except asyncio.TimeoutError:
                    print(f"Таймаут при скачивании изображения")
                    return None
        except Exception as e:
            print(f"Непредвиденная ошибка при скачивании изображения: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_category_image(self, category_name: str) -> Optional[bytes]:
        """Получает изображение категории в виде байтов"""
        try:
            # Получаем информацию о категории
            category = await self.get_category(category_name)
            # Получаем URL изображения
            image_url = self.get_image_url(category)
            if not image_url:
                return None
                
            # Скачиваем изображение
            return await self.download_image_from_url(image_url)
        except Exception as e:
            print(f"Ошибка при получении изображения категории: {str(e)}")
            return None 