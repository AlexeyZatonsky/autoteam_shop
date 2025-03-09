from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


class ProductCreationState(BaseModel):
    """Состояние создания продукта в боте"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)  # Список file_id фотографий

    def is_complete(self) -> bool:
        """Проверяет, заполнены ли все необходимые поля"""
        return all([
            self.name,
            self.price is not None,
            len(self.categories) > 0,
            len(self.photos) > 0
        ]) 