from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from src.database import Base


# Таблица связи между корзиной и продуктами
cart_products = Table(
    "cart_products",
    Base.metadata,
    Column("cart_id", UUID(as_uuid=True), ForeignKey("carts.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("quantity", Integer, default=1, nullable=False),
)


class Cart(Base):
    """Модель корзины пользователя"""
    __tablename__ = "carts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # ID пользователя в Telegram
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Отношение к продуктам через таблицу связи
    products = relationship(
        "Product", 
        secondary=cart_products, 
        lazy="joined",
        backref="carts"
    )
    
    # Отношение к элементам корзины (для хранения количества)
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    """Модель элемента корзины (продукт + количество)"""
    __tablename__ = "cart_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    price_at_add = Column(Float, nullable=False)  # Цена на момент добавления в корзину
    
    # Отношения
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
