from pydantic import BaseModel, UUID4, Field
from decimal import Decimal
from datetime import datetime
from typing import List
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum


class OrderItemBase(BaseModel):
    product_id: UUID4
    quantity: int
    price: Decimal = Field(decimal_places=2)
    product_name: str


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: UUID4
    order_id: UUID4

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    payment_status: PaymentStatusEnum = Field(
        default=PaymentStatusEnum.NOT_PAID,
        description="Статус оплаты заказа"
    )
    delivery_method: DeliveryMethodEnum = Field(
        description="Способ доставки"
    )
    phone_number: str = Field(
        min_length=10,
        max_length=20,
        pattern="^[+]?[0-9]+$",
        description="Номер телефона в международном формате"
    )
    delivery_address: str | None = Field(
        default=None,
        min_length=10,
        description="Адрес доставки"
    )
    telegram_username: str = Field(
        min_length=5,
        description="Имя пользователя в Telegram"
    )


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: OrderStatusEnum | None = None
    payment_status: PaymentStatusEnum | None = None
    delivery_method: DeliveryMethodEnum | None = None
    phone_number: str | None = None
    delivery_address: str | None = None


class OrderResponse(OrderBase):
    id: UUID4
    user_id: str
    total_amount: Decimal = Field(decimal_places=2)
    status: OrderStatusEnum
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
