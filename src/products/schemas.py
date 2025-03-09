from pydantic import BaseModel, Field, UUID4, constr, confloat
from typing import List, Optional
from decimal import Decimal
from ..categories.schemas import CategoryRead
from fastapi import UploadFile



class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Название продукта")
    description: Optional[str] = Field(None, max_length=1000, description="Описание продукта")
    price: Decimal = Field(..., ge=0, le=999999.99, description="Цена продукта")
    images: Optional[List[str]] = Field(default=None, description="Список относительных путей к изображениям")
    is_available: bool = Field(default=True, description="Доступность продукта")


class ProductCreate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Название продукта")
    description: Optional[str] = Field(None, max_length=1000, description="Описание продукта")
    price: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="Цена продукта")
    categories: List[str] = Field(default_factory=list, description="Список названий категорий")
    images: List[str] = Field(default_factory=list, description="Список относительных путей к изображениям")
    
    def validate_for_api(self) -> bool:
        """Проверяет, готова ли модель для отправки в API"""
        return all([
            self.name is not None and len(self.name) >= 2,
            self.price is not None and self.price > 0,
            len(self.categories) > 0,
            len(self.images) > 0,
        ])

    class Config:
        arbitrary_types_allowed = True


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, ge=0, le=999999.99)
    images: Optional[List[str]] = None
    is_available: Optional[bool] = None
    categories: Optional[List[str]] = Field(None, min_items=1)


class ProductRead(ProductBase):
    id: UUID4
    categories: List[CategoryRead]

    class Config:
        from_attributes = True


# Схемы для фильтрации и поиска
class ProductFilter(BaseModel):
    category_name: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, le=999999.99)
    is_available: Optional[bool] = None
    search_query: Optional[str] = Field(None, min_length=2)


# Схемы для ответов API
class ProductListResponse(BaseModel):
    items: List[ProductRead]
    total: int
    page: int
    size: int
    pages: int
