from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UUID, Enum
from ..database import Base
import uuid
from .enums import OrderStatusEnum, PaymentMethodEnum, DeliveryMethodEnum




class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(OrderStatusEnum), nullable=False)
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False)
    delivery_method = Column(Enum(DeliveryMethodEnum), nullable=False)
    phone_number = Column(String, nullable=False)
    delivery_address = Column(String, nullable=True)
    telegram_username = Column(String, nullable=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  