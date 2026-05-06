from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from nox_backend.core.database import Base


# ─────────────────────────────────────────────
# 👤 User Model
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(username={self.username})>"


# ─────────────────────────────────────────────
# 🧠 Future-Proof Models (optional, ready for NOX)
# ─────────────────────────────────────────────

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryLog(Base):
    __tablename__ = "memory_logs"

    id = Column(Integer, primary_key=True)
    key = Column(String, index=True)
    value = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)