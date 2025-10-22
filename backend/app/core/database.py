from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine with enhanced configuration
# Configure connect_args based on database type
connect_args = {}
if "postgresql" in settings.DATABASE_URL:
    connect_args = {"options": "-c timezone=utc"}
elif "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=settings.DEBUG, # Log SQL queries in debug mode
    connect_args=connect_args
)

# Session configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)

# Declarative base for all models
Base = declarative_base()


# Database event listeners
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database-specific configurations on connection"""
    if "postgresql" in settings.DATABASE_URL:
        # PostgreSQL specific settings
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC'")
    elif "sqlite" in settings.DATABASE_URL:
        # SQLite specific settings
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")


class DatabaseSession:
    """Enhanced database session with context manager support"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.error(f"Database session rolled back due to: {exc_val}")
        else:
            self.session.commit()
        self.session.close()


def get_db():
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> DatabaseSession:
    """Get a database session with context manager support"""
    return DatabaseSession()


# Database utilities
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped!")


def check_connection():
    """Check database connection health"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection is healthy")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
