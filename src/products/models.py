from sqlalchemy import Column, String, TEXT, NUMERIC, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from ..database import Base
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from ..categories.models import Category


class ProductCategory(Base):
    __tablename__ = "product_categories"
    
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
    category_name = Column(String, ForeignKey('categories.name', ondelete='CASCADE'), primary_key=True)
    

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(TEXT, nullable=True)
    price = Column(NUMERIC(10, 2), nullable=False)
    images = Column(ARRAY(String), nullable=True)
    is_available = Column(Boolean, default=True)
    
    categories = relationship('Category', secondary='product_categories')
