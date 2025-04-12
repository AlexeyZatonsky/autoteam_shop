from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, date, timedelta

from ..database import get_async_session
from ..auth.router import get_current_user, check_admin_access
from ..auth.models import Users
from ..auth.schemas import UserResponse
from ..cart.service import CartService
from .service import OrderService
from .schemas import OrderCreate, OrderUpdate, OrderResponse
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum, PaymentMethodEnum


router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


async def get_cart_service(
    session: AsyncSession = Depends(get_async_session)
) -> CartService:
    return CartService(session)


async def get_order_service(
    session: AsyncSession = Depends(get_async_session),
    cart_service: CartService = Depends(get_cart_service)
) -> OrderService:
    """Получение сервиса для работы с заказами."""
    return OrderService(session, cart_service)


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Создание нового заказа из корзины пользователя.
    
    - Требует авторизации
    - Создает заказ на основе текущей корзины пользователя
    - После создания заказа корзина очищается
    """
    return await order_service.create_order_from_cart(current_user, order_data)


@router.get("/all", response_model=List[OrderResponse])
async def get_all_orders(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка всех заказов с пагинацией.
    
    - Требует административные права
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_all_orders(skip, limit)


@router.get("", response_model=List[OrderResponse])
async def get_user_orders(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов пользователя.
    
    - Требует авторизации
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_user_orders(current_user, skip, limit)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Получение детальной информации о заказе.
    
    - Требует авторизации
    - Возвращает информацию о заказе, включая список товаров
    - Доступ только к своим заказам
    """
    order = await order_service.get_order_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Обновление информации о заказе.
    
    - Требует авторизации
    - Для обычных пользователей: только отмена заказа
    - Для администраторов: изменение статуса, способа оплаты и доставки
    """
    order = await order_service.get_order_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем права доступа
    if not current_user.is_admin():
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")
        # Пользователь может только отменить заказ
        if order_data.status and order_data.status != OrderStatusEnum.CANCELLED:
            raise HTTPException(status_code=403, detail="Можно только отменить заказ")
        # И только если заказ в статусе NEW
        if order.status != OrderStatusEnum.NEW:
            raise HTTPException(status_code=400, detail="Можно отменить только новый заказ")
    
    return await order_service.update_order(order_id, order_data)


@router.patch("/admin/order/{order_id}", response_model=OrderResponse)
async def update_order_admin(
    order_id: UUID,
    order_data: OrderUpdate,
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Обновление информации о заказе (для администраторов).
    
    - Требует прав администратора
    - Позволяет изменять статус, способ оплаты и доставки
    """
    order = await order_service.get_order_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    return await order_service.update_order(order_id, order_data)


# Маршруты для администраторов

@router.get("/admin/all", response_model=List[OrderResponse])
async def get_all_orders(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка всех заказов (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_all_orders(skip, limit)


@router.get("/admin/by-username", response_model=List[OrderResponse])
async def get_orders_by_username(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    username: str = Query(..., description="Имя пользователя в Telegram"),
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов по имени пользователя (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_orders_by_username(username, skip, limit)


@router.get("/admin/by-status", response_model=List[OrderResponse])
async def get_orders_by_status(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    status: OrderStatusEnum = Query(..., description="Статус заказа"),
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов по статусу (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_orders_by_status(status, skip, limit)


@router.get("/admin/by-date-range", response_model=List[OrderResponse])
async def get_orders_by_date_range(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    start_date: date = Query(..., description="Начальная дата"),
    end_date: date = Query(..., description="Конечная дата"),
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов за указанный период (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    # Преобразуем даты в datetime для корректного сравнения
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    return await order_service.get_orders_by_date_range(start_datetime, end_datetime, skip, limit)


@router.get("/admin/today", response_model=List[OrderResponse])
async def get_today_orders(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов за сегодня (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    today = datetime.now().date()
    start_datetime = datetime.combine(today, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())
    
    return await order_service.get_orders_by_date_range(start_datetime, end_datetime, skip, limit)


@router.get("/admin/week", response_model=List[OrderResponse])
async def get_week_orders(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов за последнюю неделю (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    start_datetime = datetime.combine(week_ago, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())
    
    return await order_service.get_orders_by_date_range(start_datetime, end_datetime, skip, limit)


@router.get("/admin/completed", response_model=List[OrderResponse])
async def get_completed_orders(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка завершенных заказов (только для администраторов).
    
    - Требует прав администратора
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_orders_by_status(OrderStatusEnum.COMPLETED, skip, limit)


@router.delete("/admin/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Удаление заказа (только для администраторов).
    
    - Требует прав администратора
    - Полностью удаляет заказ из базы данных
    """
    await order_service.delete_order(order_id)
    return {"status": "success"}


@router.delete("/admin/completed", status_code=status.HTTP_200_OK)
async def delete_completed_orders(
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Удаление всех завершенных заказов (только для администраторов).
    
    - Требует прав администратора
    - Полностью удаляет все завершенные заказы из базы данных
    """
    count = await order_service.delete_completed_orders()
    return {"status": "success", "count": count}


@router.get("/delivery-methods", response_model=List[str])
async def get_delivery_methods():
    """
    Получение списка доступных способов доставки.
    """
    return [method.value for method in DeliveryMethodEnum]


@router.get("/payment-statuses", response_model=List[str])
async def get_payment_statuses():
    """
    Получение списка возможных статусов оплаты.
    """
    return [status.value for status in PaymentStatusEnum]


@router.get("/order-statuses", response_model=List[str])
async def get_order_statuses():
    """
    Получение списка возможных статусов заказа.
    """
    return [status.value for status in OrderStatusEnum]


@router.get("/admin/order/{order_id}", response_model=OrderResponse)
async def get_order_admin(
    order_id: UUID,
    admin: Annotated[UserResponse, Depends(check_admin_access)],
    order_service: Annotated[OrderService, Depends(get_order_service)]
):
    """
    Получение детальной информации о заказе (для администраторов).
    
    - Требует прав администратора
    - Возвращает информацию о заказе, включая список товаров
    - Доступ к любому заказу
    """
    order = await order_service.get_order_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@router.get("/payment-methods", response_model=List[str])
async def get_payment_methods():
    """
    Получение списка возможных методов оплаты.
    """
    return [method.value for method in PaymentMethodEnum]
