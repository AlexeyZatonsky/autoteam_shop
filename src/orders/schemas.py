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


class OrderCreate(BaseModel):
    delivery_method: str
    payment_method: Optional[str] = None
    phone_number: str
    delivery_address: str
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        
        # Преобразование строковых значений в значения перечислений
        if data.get('delivery_method'):
            # Найти значение по ключу или искать ключ по значению
            for enum_key, enum_value in DeliveryMethodEnum.__members__.items():
                if data['delivery_method'] == enum_key or data['delivery_method'] == enum_value.value:
                    data['delivery_method'] = enum_key
                    break
                    
        if data.get('payment_method'):
            # Найти значение по ключу или искать ключ по значению
            for enum_key, enum_value in PaymentMethodEnum.__members__.items():
                if data['payment_method'] == enum_key or data['payment_method'] == enum_value.value:
                    data['payment_method'] = enum_key
                    break
                    
        return data


class OrderItemResponse(OrderItemBase):
    id: UUID4
    order_id: UUID4

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    status: OrderStatusEnum | None = None
    payment_status: PaymentStatusEnum | None = None
    delivery_method: DeliveryMethodEnum | None = None
    payment_method: PaymentMethodEnum | None = None
    phone_number: str | None = None
    delivery_address: str | None = None