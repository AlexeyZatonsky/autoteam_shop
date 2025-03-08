from pydantic import BaseModel, UUID4, Field
from decimal import Decimal
from .enums import OrderStatusEnum, PaymentMethodEnum, DeliveryMethodEnum


class OrderBase(BaseModel):
    payment_method: PaymentMethodEnum
    delivery_method: DeliveryMethodEnum
    phone_number: str
    delivery_address: str | None = None
    telegram_username: str


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: OrderStatusEnum | None = None
    payment_method: PaymentMethodEnum | None = None
    delivery_method: DeliveryMethodEnum | None = None
    phone_number: str | None = None
    delivery_address: str | None = None


class OrderResponse(OrderBase):
    id: UUID4
    user_id: UUID4
    total_amount: Decimal = Field(decimal_places=2)
    status: OrderStatusEnum

    class Config:
        from_attributes = True
