from sqlalchemy import Column, Integer, String, UUID, ForeignKey, TIMESTAMP, NUMERIC, Enum as SQLAlchemyEnum
from datetime import datetime

from sqlalchemy.orm import relationship
import uuid
from ..database import Base
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum, PaymentMethodEnum



class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # ID пользователя в Telegram
    telegram_username = Column(String, nullable=False, index=True)  # Имя пользователя в Telegram
    full_name = Column(String, nullable=False)  # Полное имя получателя заказа
    total_amount = Column(NUMERIC(10, 2), nullable=False)
    status = Column(SQLAlchemyEnum(OrderStatusEnum, native_enum=True), nullable=False, default=OrderStatusEnum.NEW)
    payment_status = Column(SQLAlchemyEnum(PaymentStatusEnum, native_enum=True), nullable=False, default=PaymentStatusEnum.NOT_PAID)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodEnum, native_enum=True), nullable=True, default=PaymentMethodEnum.PAYMENT_ON_DELIVERY)  # Способ оплаты
    delivery_method = Column(SQLAlchemyEnum(DeliveryMethodEnum, native_enum=True), nullable=False)
    phone_number = Column(String, nullable=False)
    delivery_address = Column(String, nullable=False)  # Делаем адрес доставки обязательным
    created_at = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.now(), onupdate=datetime.now(), nullable=False)
    
    # Отношения
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)  # Сохраняем название товара на момент заказа
    quantity = Column(Integer, nullable=False)
    price = Column(NUMERIC(10, 2), nullable=False)  # Цена на момент заказа
    
    
    # Отношения
    order = relationship("Order", back_populates="items")
    product = relationship("Product")