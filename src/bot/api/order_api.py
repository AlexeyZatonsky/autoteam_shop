from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import uuid
from ..api_client import APIClient
from ...settings.config import settings


class OrderAPI:
    """Класс для работы с API заказов"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.api_key = settings.BOT_API_KEY
    
    async def get_all_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список всех заказов"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/all",
            params={"skip": skip, "limit": limit},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_order(self, order_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Получает детали заказа по ID"""
        return await self.api_client.make_request(
            method="GET",
            endpoint=f"/api/orders/admin/order/{order_id}",
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_orders_by_username(self, username: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов по имени пользователя в Telegram"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/by-username",
            params={"username": username, "skip": skip, "limit": limit},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_orders_by_status(self, status: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов по статусу"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/by-status",
            params={"status": status, "skip": skip, "limit": limit},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_orders_by_date_range(self, start_date: date, end_date: date, 
                                     skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов за указанный период"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/by-date-range",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "skip": skip,
                "limit": limit
            },
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_today_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов за сегодня"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/today",
            params={"skip": skip, "limit": limit},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_week_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов за неделю"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/week",
            params={"skip": skip, "limit": limit},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_completed_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список завершенных заказов"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/orders/admin/completed",
            params={"skip": skip, "limit": limit},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def update_order_status(self, order_id: Union[str, uuid.UUID], status: str) -> Dict[str, Any]:
        """Обновляет статус заказа"""
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"/api/orders/admin/order/{order_id}",
            data={"status": status},
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key}
        )
    
    async def update_payment_status(self, order_id: Union[str, uuid.UUID], payment_status: str) -> Dict[str, Any]:
        """Обновляет статус оплаты заказа"""
        return await self.api_client.make_request(
            method="PATCH",
            endpoint=f"/api/orders/admin/order/{order_id}",
            data={"payment_status": payment_status},
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key}
        )
    
    async def delete_order(self, order_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Удаляет заказ"""
        return await self.api_client.make_request(
            method="DELETE",
            endpoint=f"/api/orders/admin/{order_id}",
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def delete_completed_orders(self) -> Dict[str, Any]:
        """Удаляет все завершенные заказы"""
        return await self.api_client.make_request(
            method="DELETE",
            endpoint="/api/orders/admin/completed",
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )
    
    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Получает информацию о пользователе по его имени пользователя в Telegram"""
        return await self.api_client.make_request(
            method="GET",
            endpoint="/api/auth/users/by-username",
            params={"username": username},
            headers={"Accept": "application/json", "X-API-Key": self.api_key}
        )