from pydantic import BaseModel, Field
from typing import Optional


class CategoryBase(BaseModel):
    """Базовая схема категории"""
    name: str = Field(..., min_length=2, max_length=100)
    image: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Схема для создания категории"""
    pass


class CategoryUpdate(CategoryBase):
    """Схема для обновления категории"""
    pass


class CategoryRead(CategoryBase):
    """Схема для чтения категории"""
    class Config:
        from_attributes = True 

