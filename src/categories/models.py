from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from ..database import Base


class Category(Base):
    __tablename__ = "categories"
    
    name = Column(String(255), primary_key=True)
    image = Column(String(500), nullable=True)  # URL изображения в S3
    
