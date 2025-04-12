from pydantic import BaseModel, UUID4, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum, PaymentMethodEnum


class OrderItemBase(BaseModel):
    product_id: UUID4
    quantity: int
    price: Decimal = Field(decimal_places=2)
    product_name: str
    


class OrderCreate(BaseModel):
    delivery_method: DeliveryMethodEnum = Field(default=DeliveryMethodEnum.SDEK)
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.PAYMENT_ON_DELIVERY)
    phone_number: str
    delivery_address: str
    
    model_config = ConfigDict(use_enum_values=True)


class OrderItemResponse(OrderItemBase):
    id: UUID4
    order_id: UUID4

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class OrderResponse(BaseModel):
    id: UUID4
    user_id: str
    telegram_username: str
    total_amount: Decimal = Field(decimal_places=2)
    status: OrderStatusEnum
    payment_status: PaymentStatusEnum
    delivery_method: DeliveryMethodEnum
    payment_method: Optional[PaymentMethodEnum] = None
    phone_number: str
    delivery_address: str | None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class OrderUpdate(BaseModel):
    status: OrderStatusEnum
    payment_status: PaymentStatusEnum
    delivery_method: DeliveryMethodEnum
    payment_method: PaymentMethodEnum
    phone_number: str
    delivery_address: str
    
    model_config = ConfigDict(use_enum_values=True)