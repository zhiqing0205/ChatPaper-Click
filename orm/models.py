from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    abstract = Column(String, default=None, index=True)
    authors = Column(String, default=None, index=True)
    keywords = Column(String, default=None, index=True)
    content = Column(String, default=None, index=True)
    analysis_result = Column(String, default=None, index=True)
    md5_hash = Column(String, index=True)
    path = Column(String, index=True)
    created_at = Column(String, index=True)
    updated_at = Column(String, index=True)