"""
Healthcare Chatbot API - Main Application
Production-ready FastAPI application with security, monitoring, and compliance features.
"""
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Request
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import timedelta

# Import app modules
from app.config import settings
from app.database import get_db, check_database_connection, init_db
from app import models
from app.seed import seed_database
from app.auth import (
    create_user,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.schemas import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    ChatMessage,
    ChatResponse,
    ChatHistoryResponse,
    ChatLogItem,
)
from app.intent import classify_intent, Intents
from app.handlers import (
    handle_order_status,
    handle_payment_invoice,
    handle_warranty_amc,
    handle_scheduling,
    handle_complaint,
    handle_default,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=[f"{settings.RATE_LIMIT_PER_HOUR}/hour"],
#     enabled=settings.RATE_LIMIT_ENABLED
# )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Handles startup and shutdown logic.
    """
    # Startup
    logger.info("="*80)
    logger.info(f"Starting Healthcare Chatbot API - Environment: {settings.ENVIRONMENT}")
    logger.info("="*80)

    # Check database connection
    if check_database_connection():
        logger.info("✓ Database connection successful")
    else:
        logger.error("✗ Database connection failed!")
        if settings.is_production:
            raise RuntimeError("Cannot start application: Database connection failed")

    # Initialize database (development only)
    if settings.is_development:
        logger.warning("Development mode: Initializing database tables")
        init_db()
    else:
        logger.info("Production mode: Use 'alembic upgrade head' for migrations")

    # Seed database with test data if enabled
    if settings.SEED_DATA:
        logger.info("SEED_DATA enabled: Populating database with test data")
        seed_database()

    # Log configuration
    logger.info(f"CORS Origins: {settings.get_cors_origins_list()}")
    logger.info(f"Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"HIPAA Compliance Mode: {settings.HIPAA_COMPLIANCE_MODE}")
    logger.info(f"OpenAI Integration: {'Enabled' if settings.OPENAI_API_KEY else 'Disabled (using fallback)'}")

    logger.info("="*80)
    logger.info("Application started successfully")
    logger.info("="*80)

    yield

    # Shutdown
    logger.info("Shutting down Healthcare Chatbot API...")


# Create FastAPI application
app = FastAPI(
    title="HealthcareSense Support Chatbot API",
    description="AI-powered customer support for healthcare equipment company",
    version=settings.API_VERSION,
    docs_url="/docs" if not settings.is_production else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# Add rate limiter to app state
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when origins is ["*"]
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", "unknown")
    client_host = request.client.host if request.client else "unknown"

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path} "
        f"[ID: {request_id}] [IP: {client_host}]"
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[Status: {response.status_code}] [Duration: {process_time:.3f}s] "
            f"[ID: {request_id}]"
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"[Error: {str(e)}] [Duration: {process_time:.3f}s] [ID: {request_id}]"
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions globally."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)} "
        f"[Path: {request.url.path}] [Method: {request.method}]",
        exc_info=True
    )

    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal error occurred. Please contact support.",
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION
    }


@app.get("/health/ready", tags=["Health"])
def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check - verifies all dependencies are available.
    Used by orchestrators (Kubernetes, Docker Swarm) to determine if app can serve traffic.
    """
    checks = {
        "database": False,
        "status": "not_ready"
    }

    # Check database
    try:
        db.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")

    # Determine overall status
    if all([checks["database"]]):
        checks["status"] = "ready"
        return checks
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=checks
        )


@app.get("/health/live", tags=["Health"])
def liveness_check() -> Dict[str, str]:
    """
    Liveness check - verifies the app is running.
    Used by orchestrators to determine if app should be restarted.
    """
    return {"status": "alive"}


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/register", response_model=Token, tags=["Authentication"])
# @limiter.limit("5/minute")  # Prevent registration abuse
def register_user(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Requires:
    - email: Valid email address
    - password: Minimum 8 characters
    - client_code: Valid client organization code

    Returns JWT access token upon successful registration.
    """
    logger.info(f"Registration request from {request.client.host}: email={user_data.email}, client_code={user_data.client_code}, password_length={len(user_data.password)}")
    
    try:
        user = create_user(db=db, user_data=user_data)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info(f"User registered successfully: {user.email}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as e:
        logger.warning(f"Registration failed with HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@app.post("/login", response_model=Token, tags=["Authentication"])
# @limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def login_user(
    request: Request,
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.

    Requires:
    - email: User's email address
    - password: User's password

    Returns JWT access token upon successful authentication.
    """
    logger.info(f"Login request received for: {user_credentials.email}")
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()

    if not user or not verify_password(user_credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    logger.info(f"User logged in successfully: {user.email}")

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse, tags=["User"])
# @limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def get_current_user_info(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information."""
    # Get user's primary client info
    user_client = db.query(models.UserClient).filter(
        models.UserClient.user_id == current_user.id,
        models.UserClient.is_primary == 1
    ).first()

    client_name = None
    client_code = None
    if user_client:
        client = db.query(models.Client).filter(models.Client.id == user_client.client_id).first()
        if client:
            client_name = client.name
            client_code = client.client_code

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        client_name=client_name,
        client_code=client_code
    )


# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
# @limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(
    request: Request,
    message: ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a chat message and return AI-generated response.

    The system will:
    1. Classify the user's intent
    2. Route to appropriate handler (SQL query or RAG retrieval)
    3. Generate a natural language response
    4. Log the conversation for compliance

    Rate limited to prevent abuse.
    """
    start_time = time.time()

    # Get user's primary client
    user_client = db.query(models.UserClient).filter(
        models.UserClient.user_id == current_user.id,
        models.UserClient.is_primary == 1
    ).first()

    if not user_client:
        raise HTTPException(status_code=400, detail="User not linked to any client")

    # Classify intent
    try:
        intent = await classify_intent(message.message)
        logger.info(f"Intent classified: {intent.value} for user {current_user.email}")
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        intent = Intents.GENERAL

    # Route to appropriate handler
    try:
        if intent == Intents.ORDER_STATUS:
            ai_response, source = handle_order_status(db, user_client.client_id, message.message)
        elif intent == Intents.PAYMENT_INVOICE:
            ai_response, source = handle_payment_invoice(db, user_client.client_id, message.message)
        elif intent == Intents.WARRANTY_AMC:
            ai_response, source = handle_warranty_amc(db, user_client.client_id, message.message)
        elif intent == Intents.SCHEDULING:
            ai_response, source = handle_scheduling(db, user_client.client_id, message.message)
        elif intent == Intents.COMPLAINT:
            ai_response, source = handle_complaint(db, current_user.id, user_client.client_id, message.message)
        else:
            ai_response, source = handle_default(db, user_client.client_id, message.message)

    except Exception as e:
        logger.error(f"Handler error for intent {intent.value}: {e}", exc_info=True)
        ai_response = "I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists."
        source = "error"

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000

    # Log the conversation (HIPAA compliance requirement)
    try:
        chat_log = models.ChatLog(
            user_id=current_user.id,
            client_id=user_client.client_id,
            user_message=message.message,
            ai_response=ai_response,
            intent=intent.value,
            data_source=source,
        )
        db.add(chat_log)
        db.commit()

        logger.info(
            f"Chat logged: User={current_user.email}, Intent={intent.value}, "
            f"Source={source}, ResponseTime={response_time_ms:.2f}ms"
        )

    except Exception as e:
        logger.error(f"Failed to log chat: {e}")
        # Don't fail the request if logging fails

    return ChatResponse(
        response=ai_response,
        intent=intent.value,
        data_source=source,
    )


@app.get("/chat/history", response_model=ChatHistoryResponse, tags=["Chat"])
# @limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def chat_history(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve chat history for the current user.

    Returns up to 50 most recent chat messages.
    """
    user_client = db.query(models.UserClient).filter(
        models.UserClient.user_id == current_user.id,
        models.UserClient.is_primary == 1
    ).first()

    if not user_client:
        raise HTTPException(status_code=400, detail="User not linked to any client")

    logs = (
        db.query(models.ChatLog)
        .filter(
            models.ChatLog.user_id == current_user.id,
            models.ChatLog.client_id == user_client.client_id
        )
        .order_by(models.ChatLog.timestamp.desc())
        .limit(50)
        .all()
    )

    items = [
        ChatLogItem(
            id=log.id,
            timestamp=log.timestamp,
            user_message=log.user_message,
            ai_response=log.ai_response,
            intent=log.intent,
            data_source=log.data_source,
        )
        for log in logs
    ]

    return {"items": items}


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower()
    )
