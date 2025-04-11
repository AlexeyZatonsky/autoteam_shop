from pydantic import BaseModel, UUID4, Field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum, PaymentMethodEnum


class OrderItemBase(BaseModel):
    product_id: UUID4
    quantity: int
    price: Decimal = Field(decimal_places=2)
    product_name: str


class OrderBase(BaseModel):
    delivery_method: DeliveryMethodEnum
    payment_method: Optional[PaymentMethodEnum] = None



class OrderCreate(OrderBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: UUID4
    order_id: UUID4

    class Config:
        from_attributes = True


class OrderResponse(OrderBase):
    id: UUID4
    user_id: str
    telegram_username: str
    total_amount: Decimal = Field(decimal_places=2)
    status: OrderStatusEnum
    payment_status: PaymentStatusEnum
    phone_number: str
    delivery_address: str | None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    status: OrderStatusEnum | None = None
    payment_status: PaymentStatusEnum | None = None
    delivery_method: DeliveryMethodEnum | None = None
    phone_number: str | None = None
    delivery_address: str | None = None
    payment_method: PaymentMethodEnum | None = None