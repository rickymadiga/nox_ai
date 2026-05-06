from sqlalchemy import Column, Integer, String
from nox_backend.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)   # ← ADD THIS LINE
    password = Column(String, nullable=False)
    
    # Optional fields (uncomment if you need them later)
    # failed_attempts = Column(Integer, default=0)
    # lock_until = Column(Float, default=0)
    # auto_recharge = Column(Integer, default=0)
    # authorization_code = Column(String)
    # last4 = Column(String)
    # card_brand = Column(String)