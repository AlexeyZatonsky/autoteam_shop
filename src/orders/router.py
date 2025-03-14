from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ..database import get_async_session
from ..auth.router import get_current_user
from ..auth.models import Users
from ..cart.service import CartService
from .service import OrderService
from .schemas import OrderCreate, OrderUpdate, OrderResponse
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum


router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


def get_order_service(
    session: AsyncSession = Depends(get_async_session),
    cart_service: CartService = Depends(CartService)
) -> OrderService:
    """Получение сервиса для работы с заказами."""
    return OrderService(session, cart_service)


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: Annotated[Users, Depends(get_current_user)],
    order_service: OrderService = Depends(get_order_service)
):
    """
    Создание нового заказа из корзины пользователя.
    
    - Требует авторизации
    - Создает заказ на основе текущей корзины пользователя
    - После создания заказа корзина очищается
    """
    return await order_service.create_order_from_cart(current_user.id, order_data)


@router.get("", response_model=List[OrderResponse])
async def get_user_orders(
    current_user: Annotated[Users, Depends(get_current_user)],
    order_service: OrderService = Depends(get_order_service),
    skip: int = 0,
    limit: int = 10
):
    """
    Получение списка заказов пользователя.
    
    - Требует авторизации
    - Поддерживает пагинацию через параметры skip и limit
    - Заказы сортируются по дате создания (сначала новые)
    """
    return await order_service.get_user_orders(current_user.id, skip, limit)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: Annotated[Users, Depends(get_current_user)],
    order_service: OrderService = Depends(get_order_service)
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
    current_user: Annotated[Users, Depends(get_current_user)],
    order_service: OrderService = Depends(get_order_service)
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
        if order_data.order_status and order_data.order_status != OrderStatusEnum.CANCELLED:
            raise HTTPException(status_code=403, detail="Можно только отменить заказ")
        # И только если заказ в статусе NEW
        if order.status != OrderStatusEnum.NEW:
            raise HTTPException(status_code=400, detail="Можно отменить только новый заказ")
    
    return await order_service.update_order(order_id, order_data)


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
