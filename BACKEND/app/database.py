from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from core.config import settings

# Database configuration - using SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", settings.database_url)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Create tables
def create_tables():
    # Create tables with checkfirst=True to avoid errors if tables already exist
    Base.metadata.create_all(bind=engine, checkfirst=True)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()