from sqlalchemy import create_engine, Column, String, Boolean, ForeignKey, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    profile_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    email = Column(String, nullable=True)
    accepted_terms = Column(Boolean, default=False)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=func.now())
    
class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("users.profile_id"))
    question = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=func.now())