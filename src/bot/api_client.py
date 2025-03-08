import aiohttp
from typing import Any, Dict


class APIClient:
    def __init__(self, api_url: str):
        self.api_url = api_url

    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение запроса к API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"API error: {response.status} - {error_text}")
                return await response.json() 