from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager
from sqlalchemy.orm import Session

DATABASE_URL = "sqlite:///./nox.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Important for SQLite
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()