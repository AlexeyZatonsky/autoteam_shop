from pydantic import BaseModel, Field, UUID4
from typing import List, Optional
from datetime import datetime


class CartItemBase(BaseModel):
    """Базовая схема элемента корзины"""
    product_id: UUID4
    quantity: int = Field(ge=1, default=1)


class CartItemCreate(CartItemBase):
    """Схема для создания элемента корзины"""
    pass


class CartItemUpdate(BaseModel):
    """Схема для обновления элемента корзины"""
    quantity: Optional[int] = Field(ge=1, default=None)


class CartItemResponse(CartItemBase):
    """Схема ответа для элемента корзины"""
    id: UUID4
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


class CartCreate(CartBase):
    """Схема для создания корзины"""
    pass


class CartResponse(CartBase):
    """Схема ответа для корзины"""
    id: UUID4
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class CartDetailResponse(CartResponse):
    """Детальная схема ответа для корзины с элементами"""
    items: List[CartItemDetailResponse] = []
    total_price: float
    
    class Config:
        from_attributes = True
