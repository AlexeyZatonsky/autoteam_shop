from sqlalchemy import Column, String, Numeric, UUID, ARRAY, Boolean, ForeignKey, TEXT
from ..database import Base
import uuid




class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    images = Column(ARRAY(String), nullable=True)  # массив URL изображений
    is_available = Column(Boolean, default=True)
    
    
class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)