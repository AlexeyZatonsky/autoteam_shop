import aiohttp
from typing import Any, Dict, Optional, List, Union
from urllib.parse import urljoin


class APIClient:
    def __init__(self, api_url: str):
        # Убеждаемся, что URL заканчивается на /
        self.api_url = api_url if api_url.endswith('/') else f"{api_url}/"

    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Union[Dict[str, Any], aiohttp.FormData] = None,
        files: List[tuple] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Выполнение запроса к API
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Эндпоинт API (без начального слеша)
            data: Данные для запроса (dict или FormData)
            files: Список кортежей (name, (filename, file_content, content_type))
            **kwargs: Дополнительные параметры для запроса
        """
        # Убираем начальный слеш, если он есть
        endpoint = endpoint.lstrip('/')
        # Формируем полный URL
        url = urljoin(self.api_url, endpoint)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Если передан FormData, используем его как есть
                if isinstance(data, aiohttp.FormData):
                    kwargs['data'] = data
                    print(f"Отправляем FormData на {url}")
                    
                    # Добавляем отладочную информацию
                    for field in data._fields:
                        field_name, headers, value = field
                        print(f"Поле формы: {field_name}, заголовки: {headers}, тип значения: {type(value)}")
                        
                # Если есть файлы, создаем FormData
                elif files:
                    form = aiohttp.FormData()
                    
                    # Добавляем обычные поля
                    if data:
                        for key, value in data.items():
                            if isinstance(value, list):
                                # Для списков добавляем каждое значение отдельно
                                for item in value:
                                    form.add_field(key, str(item))
                            else:
                                form.add_field(key, str(value))
                    
                    # Добавляем файлы
                    for file_field, file_tuple in files:
                        filename, file_content, content_type = file_tuple
                        form.add_field(
                            file_field,
                            file_content,
                            filename=filename,
                            content_type=content_type
                        )
                    
                    kwargs['data'] = form
                # Если просто данные, добавляем их как json
                elif data:
                    kwargs['json'] = data
                
                print(f"Отправляем запрос {method} на {url}")
                async with session.request(method, url, **kwargs) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        print(f"Ошибка API {response.status}: {error_text}")
                        raise Exception(f"API error {response.status}: {error_text}")
                    
                    response_text = await response.text()
                    print(f"Ответ сервера: {response_text}")
                    return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}") 