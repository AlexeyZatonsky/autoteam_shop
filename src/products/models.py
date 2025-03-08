from sqlalchemy import Column, Integer, String, ForeignKey, TEXT, NUMERIC, ARRAY, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(TEXT, nullable=True)
    
    # Отношения
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(TEXT, nullable=True)
    price = Column(NUMERIC(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    images = Column(ARRAY(String), nullable=True)  # массив URL изображений
    is_available = Column(Boolean, default=True)
    
    # Отношения
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")