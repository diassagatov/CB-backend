from sqlalchemy import Column, Integer, String, Engine
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True)
    password = Column(String(20))
    name = Column(String(20))
    surname = Column(String(20))


class Company(Base):
    __tablename__ = 'Companies'

    id = Column(Integer, primary_key=True, index=True)
    cat = Column(String(40))
    name = Column(String(40))
    Bonus = Column(Integer)
