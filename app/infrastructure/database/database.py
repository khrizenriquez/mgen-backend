"""
Database configuration and connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from typing import Generator

# Load DATABASE_URL from environment and resolve Railway placeholders
DATABASE_URL = os.getenv("DATABASE_URL")

# Railway sometimes uses {{POSTGRES_DB}} placeholder - resolve it
if DATABASE_URL and "{{POSTGRES_DB}}" in DATABASE_URL:
    postgres_db = os.getenv("POSTGRES_DB", "railway")
    DATABASE_URL = DATABASE_URL.replace("{{POSTGRES_DB}}", postgres_db)
    print(f"✅ Resolved DATABASE_URL placeholder: using database '{postgres_db}'")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Database dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()