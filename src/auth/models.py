from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TEXT, UUID
from ..database import Base
import uuid



class Users(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    tg_name = Column(String, nullable=False)
