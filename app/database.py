"""
Database configuration with production-ready settings.
Supports MySQL with connection pooling and proper error handling.
"""
from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import logging
from typing import Generator

from app.config import settings

logger = logging.getLogger(__name__)

# Determine engine parameters based on database type
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connections before using them
    "echo": settings.LOG_LEVEL == "DEBUG",  # Log SQL queries in debug mode
}

# Configure connection pooling for production databases
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "poolclass": QueuePool,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    })

    # For MySQL specifically, add connection arguments
    if "mysql" in settings.DATABASE_URL:
        engine_kwargs["connect_args"] = {
            "connect_timeout": 10,
            "charset": "utf8mb4",
        }
        # Add SSL support if needed in production
        if settings.is_production:
            # Uncomment and configure if using SSL
            # engine_kwargs["connect_args"]["ssl"] = {
            #     "ssl_ca": "/path/to/ca-cert.pem",
            #     "ssl_cert": "/path/to/client-cert.pem",
            #     "ssl_key": "/path/to/client-key.pem",
            # }
            pass
else:
    # SQLite specific configuration
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Create engine
try:
    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
    logger.info(f"Database engine created successfully for {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'SQLite'}")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


# Add event listeners for better connection management
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for new database connections."""
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Event listener when connection is checked out from pool."""
    # Test the connection is still alive
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except exc.DisconnectionError:
        # Connection is dead, invalidate it
        logger.warning("Dead connection detected, invalidating...")
        connection_record.invalidate()
        raise


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent additional queries after commit
)

# Create declarative base
Base = declarative_base()


# Dependency for FastAPI routes to get a DB session
def get_db() -> Generator:
    """
    Dependency that provides a database session.
    Automatically handles session lifecycle and cleanup.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def init_db():
    """
    Initialize database tables.
    WARNING: Only use in development! Use Alembic migrations in production.
    """
    if settings.is_production:
        logger.warning(
            "init_db() called in production! "
            "Use Alembic migrations instead: alembic upgrade head"
        )
        return

    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables created successfully")
    except Exception as e:
        # Ignore "table already exists" errors from concurrent workers
        if "already exists" in str(e):
            logger.info("Database tables already exist (created by another worker)")
        else:
            logger.error(f"Error creating database tables: {e}")
            raise
