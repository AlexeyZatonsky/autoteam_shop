from pydantic import BaseModel, Field, UUID4, HttpUrl, constr, confloat
from typing import List, Optional
from decimal import Decimal


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Название категории")


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Название продукта")
    description: Optional[str] = Field(None, max_length=1000, description="Описание продукта")
    price: Decimal = Field(..., ge=0, le=999999.99, description="Цена продукта")
    images: Optional[List[HttpUrl]] = Field(default=None, description="Список URL изображений")
    is_available: bool = Field(default=True, description="Доступность продукта")


class ProductCreate(ProductBase):
    categories: List[str] = Field(..., min_items=1, description="Список названий категорий")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, ge=0, le=999999.99)
    images: Optional[List[HttpUrl]] = None
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
