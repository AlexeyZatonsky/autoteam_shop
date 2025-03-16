from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class CartItemBase(BaseModel):
    """Базовая схема элемента корзины"""
    product_id: UUID
    quantity: int = Field(ge=1, default=1)


class CartItemCreate(CartItemBase):
    """Схема для создания элемента корзины"""
    pass


class CartItemUpdate(CartItemBase):
    """Схема для обновления элемента корзины"""
    product_id: UUID = Field(description="ID продукта")
    quantity: int = Field(description="Количество товара") # органичение 0 - полное удаление товара из корзины -1 - удаление одной единицы товара из корзины

class CartItemResponse(CartItemBase):
    """Схема ответа для элемента корзины"""
    id: UUID
    price_at_add: float
    
    class Config:
        from_attributes = True


class CartItemDetailResponse(CartItemResponse):
    """Детальная схема ответа для элемента корзины с информацией о продукте"""
    product_name: str
    product_description: Optional[str] = None
    product_image: Optional[str] = None
    
    class Config:
        from_attributes = True


class CartBase(BaseModel):
    """Базовая схема корзины"""
    user_id: str
    user_tg_name: str


class CartCreate(CartBase):
    """Схема для создания корзины"""
    pass


class CartResponse(CartBase):
    """Схема ответа для корзины"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartDetailResponse(CartResponse):
    """Детальная схема ответа для корзины с элементами"""
    items: List[CartItemDetailResponse] = []
    total_price: float
    
    class Config:
        from_attributes = True
