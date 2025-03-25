from pydantic import BaseModel, Field
from typing import Optional
from fastapi import UploadFile


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    image: Optional[str] = None


class CategoryCreate(CategoryBase):
    image: Optional[UploadFile] = None


class CategoryUpdate(BaseModel):
    image: Optional[UploadFile] = None


class CategoryRead(CategoryBase):
    class Config:
        from_attributes = True 

