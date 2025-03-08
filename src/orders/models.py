from sqlalchemy import Column, Integer, String, ForeignKey, TEXT, NUMERIC, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class OrderStatus(str, enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"


class DeliveryMethod(str, enum.Enum):
    SDEK = "sdek"
    PEK = "pek"
    BAIKAL = "baikal"
    KIT = "kit"
    BUSINESS_LINES = "business_lines"
    PICKUP = "pickup"
    POST = "post"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(NUMERIC(10, 2), nullable=False)
    status = Column(SQLAlchemyEnum(OrderStatus), nullable=False, default=OrderStatus.NEW)
    payment_method = Column(SQLAlchemyEnum(PaymentMethod), nullable=False)
    delivery_method = Column(SQLAlchemyEnum(DeliveryMethod), nullable=False)
    phone_number = Column(String, nullable=False)
    delivery_address = Column(TEXT, nullable=True)
    
    # Отношения
    items = relationship("OrderItem", back_populates="order")
    user = relationship("Users", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(NUMERIC(10, 2), nullable=False)  # цена на момент заказа
    
    # Отношения
    order = relationship("Order", back_populates="items")
    product = relationship("Product") 