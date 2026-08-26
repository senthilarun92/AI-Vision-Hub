from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from backend.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(100), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    phone = Column(String(20), nullable=True)

    role = Column(String(20), default="user")

    created_at = Column(DateTime, default=datetime.utcnow)
