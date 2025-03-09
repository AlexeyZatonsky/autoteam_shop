from sqlalchemy import Column, String
from ..database import Base


class Category(Base):
    __tablename__ = "categories"
    name = Column(String, primary_key=True) 