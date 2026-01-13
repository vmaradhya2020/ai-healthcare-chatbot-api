"""
Configuration management with validation for Healthcare Chatbot API.
Ensures all required environment variables are present and valid.
"""
import os
import secrets
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation."""

    # =============================================================================
    # SECURITY - REQUIRED
    # =============================================================================
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    # =============================================================================
    # DATABASE - REQUIRED
    # =============================================================================
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # =============================================================================
    # OPENAI API - OPTIONAL
    # =============================================================================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # =============================================================================
    # CHROMADB / RAG
    # =============================================================================
    CHROMA_DIR: str = ".chroma"
    CHROMA_COLLECTION: str = "healthcare_specs"

    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_VERSION: str = "v1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SEED_DATA: bool = False  # Set to true to populate database with test data

    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    CORS_ORIGINS: str = "http://localhost:4200"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # =============================================================================
    # LOGGING
    # =============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: Optional[str] = None

    # =============================================================================
    # MONITORING (Optional)
    # =============================================================================
    SENTRY_DSN: Optional[str] = None
    APM_ENABLED: bool = False
    APM_SERVICE_NAME: str = "healthcare-chatbot-api"

    # =============================================================================
    # COMPLIANCE
    # =============================================================================
    HIPAA_COMPLIANCE_MODE: bool = True
    CHAT_LOG_RETENTION_DAYS: int = 2555  # 7 years for HIPAA
    AUDIT_LOG_RETENTION_DAYS: int = 2555

    # =============================================================================
    # PERFORMANCE
    # =============================================================================
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 30
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_MAX_RESULTS: int = 5

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that SECRET_KEY is not a default value in production."""
        dangerous_defaults = [
            "your-secret-key-change-this-in-production",
            "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_IN_PRODUCTION",
            "change-me",
            "secret",
            "your_secret_key_here",
        ]

        # Get environment from env vars directly to avoid circular dependency
        env = os.getenv("ENVIRONMENT", "development").lower()

        if env in ["production", "prod"]:
            if not v or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            if v.lower() in dangerous_defaults:
                raise ValueError(
                    "SECRET_KEY cannot be a default value in production! "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )

        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL and warn about SQLite in production."""
        env = os.getenv("ENVIRONMENT", "development").lower()

        if env in ["production", "prod"] and v.startswith("sqlite"):
            raise ValueError(
                "SQLite is not suitable for production! "
                "Please use MySQL or PostgreSQL. "
                "Example: mysql+pymysql://user:password@localhost:3306/dbname"
            )

        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins."""
        env = os.getenv("ENVIRONMENT", "development").lower()

        if env in ["production", "prod"] and ("*" in v or "localhost" in v):
            raise ValueError(
                "CORS_ORIGINS must not contain wildcards or localhost in production!"
            )

        return v

    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() in ["production", "prod"]

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() in ["development", "dev"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """
    Get validated settings instance.
    Raises ValidationError if required settings are missing or invalid.
    """
    try:
        return Settings()
    except ValidationError as e:
        print("\n" + "="*80)
        print("CONFIGURATION ERROR: Required environment variables are missing or invalid!")
        print("="*80)
        print("\nPlease ensure you have a .env file with all required variables.")
        print("See .env.example for a template.\n")
        print("Validation errors:")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  - {field}: {error['msg']}")
        print("\n" + "="*80 + "\n")
        raise


# Global settings instance
try:
    settings = get_settings()
except ValidationError:
    # Re-raise to prevent app startup with invalid config
    raise
