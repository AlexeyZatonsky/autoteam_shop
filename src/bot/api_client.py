import aiohttp
from typing import Any, Dict, Optional, List, Union
from urllib.parse import urljoin


class APIClient:
    def __init__(self, api_url: str):
        # Убеждаемся, что URL заканчивается на /
        self.api_url = api_url if api_url.endswith('/') else f"{api_url}/"
        
        # API клиенты будут инициализированы позже
        self.product_api = None
        self.category_api = None
        self.order_api = None
        
        # Инициализируем API клиенты
        self._init_api_clients()

    def _init_api_clients(self):
        """Инициализация API клиентов"""
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from .api.product_api import ProductAPI
        from .api.category_api import CategoryAPI
        from .api.order_api import OrderAPI
        
        self.product_api = ProductAPI(self)
        self.category_api = CategoryAPI(self)
        self.order_api = OrderAPI(self)

    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Union[Dict[str, Any], aiohttp.FormData] = None,
        files: List[tuple] = None,
        is_form_data: bool = False,
        is_json: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Выполнение запроса к API
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Эндпоинт API (без начального слеша)
            data: Данные для запроса (dict или FormData)
            files: Список кортежей (name, (filename, file_content, content_type))
            is_form_data: Флаг, указывающий, что данные нужно отправить как FormData
            is_json: Флаг, указывающий, что данные нужно отправить как JSON
            **kwargs: Дополнительные параметры для запроса
        """
        # Убираем начальный слеш, если он есть
        endpoint = endpoint.lstrip('/')
        # Формируем полный URL
        url = urljoin(self.api_url, endpoint)

        connector = aiohttp.TCPConnector(ssl=False) 
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                # Если задан is_json, принудительно отправляем как JSON
                if is_json and data and not isinstance(data, aiohttp.FormData):
                    kwargs['json'] = data
                    print(f"Отправляем JSON данные на {url}: {data}")
                # Если передан FormData или указан флаг is_form_data, используем FormData
                elif isinstance(data, aiohttp.FormData) or is_form_data:
                    if not isinstance(data, aiohttp.FormData):
                        form = aiohttp.FormData()
                        for key, value in data.items():
                            form.add_field(key, str(value))
                        data = form
                    
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
                    for file_info in files:
                        if len(file_info) == 2:  # Формат (name, (filename, content, type))
                            file_field, file_tuple = file_info
                            filename, file_content, content_type = file_tuple
                            form.add_field(
                                file_field,
                                file_content,
                                filename=filename,
                                content_type=content_type
                            )
                    
                    kwargs['data'] = form
                    print(f"Отправляем файлы на {url}")
                    
                # Если просто данные, добавляем их как json
                elif data:
                    kwargs['json'] = data
                    print(f"Отправляем JSON данные на {url}: {data}")
                
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
