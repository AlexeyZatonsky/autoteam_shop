from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from src.database import Base





class Cart(Base): 
    __tablename__ = "carts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # ID пользователя в Telegram
    user_tg_name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.now(), onupdate=datetime.now(), nullable=False)
    
    # Отношение к элементам корзины с каскадным удалением
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy="subquery")
    
    # Индекс для быстрого поиска корзины по user_id
    __table_args__ = (
        Index('idx_cart_user_id', 'user_id'),
    )

class CartItem(Base): 
    __tablename__ = "cart_items"
    
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), primary_key=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    
    # Отношения
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", lazy="joined")
    
    # Индекс для быстрого поиска элементов по cart_id
    __table_args__ = (
        Index('idx_cart_item_cart_id', 'cart_id'),
    )

