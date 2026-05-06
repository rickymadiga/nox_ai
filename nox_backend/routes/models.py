from nox_backend.core.database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}   # important

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)