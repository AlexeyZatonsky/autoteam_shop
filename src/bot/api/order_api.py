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
        try:
            # Проверка наличия API ключа
            if not self.api_key:
                raise ValueError("API ключ не установлен. Проверьте настройки бота.")
            
            print(f"Отправляем запрос на получение заказов с API ключом: {self.api_key[:5]}...")
            
            headers = {
                "Accept": "application/json", 
                "X-API-Key": self.api_key
            }
            
            print(f"Заголовки запроса: {headers}")
            
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/orders/admin/all",
                params={"skip": skip, "limit": limit},
                headers=headers
            )
            
            print(f"Получен результат: {result[:100] if isinstance(result, list) else str(result)[:100]}...")
            return result
        except Exception as e:
            print(f"Ошибка при получении заказов: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def get_order(self, order_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Получает детали заказа по ID"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint=f"/api/orders/admin/order/{order_id}",
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении заказа по ID {order_id}: {str(e)}")
            # Если ошибка связана с авторизацией
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации при получении заказа")
            raise
    
    async def get_orders_by_username(self, username: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов по имени пользователя в Telegram"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/orders/admin/by-username",
                params={"username": username, "skip": skip, "limit": limit},
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении заказов по имени пользователя {username}: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def get_orders_by_status(self, status: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов по статусу"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/orders/admin/by-status",
                params={"status": status, "skip": skip, "limit": limit},
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении заказов по статусу {status}: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def get_orders_by_date_range(self, start_date: date, end_date: date, 
                                     skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов за указанный период"""
        try:
            result = await self.api_client.make_request(
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
            return result
        except Exception as e:
            print(f"Ошибка при получении заказов за период с {start_date} по {end_date}: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def get_today_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов за сегодня"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/orders/admin/today",
                params={"skip": skip, "limit": limit},
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении заказов за сегодня: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def get_week_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список заказов за неделю"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/orders/admin/week",
                params={"skip": skip, "limit": limit},
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении заказов за неделю: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def get_completed_orders(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список завершенных заказов"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/orders/admin/completed",
                params={"skip": skip, "limit": limit},
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении завершенных заказов: {str(e)}")
            # Если ошибка связана с авторизацией, возвращаем пустой список
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации. Возвращаем пустой список заказов.")
                return []
            raise
    
    async def update_order_status(self, order_id: Union[str, uuid.UUID], status: str) -> Dict[str, Any]:
        """Обновляет статус заказа"""
        try:
            # Сначала получаем полную информацию о заказе
            order = await self.get_order(order_id)
            
            if not order:
                raise ValueError(f"Заказ с ID {order_id} не найден")
            
            # Обновляем только статус заказа
            order["status"] = status
            
            # Отправляем полную информацию обратно
            return await self.api_client.make_request(
                method="PATCH",
                endpoint=f"/api/orders/admin/order/{order_id}",
                data=order,
                headers={"Content-Type": "application/json", "X-API-Key": self.api_key}
            )
        except Exception as e:
            print(f"Ошибка при обновлении статуса заказа: {str(e)}")
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации при обновлении статуса заказа")
            raise
    
    async def update_payment_status(self, order_id: Union[str, uuid.UUID], payment_status: str) -> Dict[str, Any]:
        """Обновляет статус оплаты заказа"""
        try:
            # Сначала получаем полную информацию о заказе
            order = await self.get_order(order_id)
            
            if not order:
                raise ValueError(f"Заказ с ID {order_id} не найден")
            
            # Обновляем только статус оплаты
            order["payment_status"] = payment_status
            
            # Отправляем полную информацию обратно
            return await self.api_client.make_request(
                method="PATCH",
                endpoint=f"/api/orders/admin/order/{order_id}",
                data=order,
                headers={"Content-Type": "application/json", "X-API-Key": self.api_key}
            )
        except Exception as e:
            print(f"Ошибка при обновлении статуса оплаты: {str(e)}")
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации при обновлении статуса оплаты")
            raise
    
    async def delete_order(self, order_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Удаляет заказ"""
        try:
            result = await self.api_client.make_request(
                method="DELETE",
                endpoint=f"/api/orders/admin/{order_id}",
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при удалении заказа {order_id}: {str(e)}")
            # Если ошибка связана с авторизацией
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации при удалении заказа")
            raise
    
    async def delete_completed_orders(self) -> Dict[str, Any]:
        """Удаляет все завершенные заказы"""
        try:
            result = await self.api_client.make_request(
                method="DELETE",
                endpoint="/api/orders/admin/completed",
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при удалении завершенных заказов: {str(e)}")
            # Если ошибка связана с авторизацией
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации при удалении завершенных заказов")
            raise
    
    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Получает информацию о пользователе по его имени пользователя в Telegram"""
        try:
            result = await self.api_client.make_request(
                method="GET",
                endpoint="/api/auth/users/by-username",
                params={"username": username},
                headers={"Accept": "application/json", "X-API-Key": self.api_key}
            )
            return result
        except Exception as e:
            print(f"Ошибка при получении информации о пользователе {username}: {str(e)}")
            # Если ошибка связана с авторизацией
            if "401" in str(e) or "not found" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Ошибка авторизации при получении информации о пользователе")
            # Возвращаем None вместо вызова исключения, так как эта информация не критична
            return None