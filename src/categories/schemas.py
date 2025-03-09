from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Название категории")


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    class Config:
        from_attributes = True 