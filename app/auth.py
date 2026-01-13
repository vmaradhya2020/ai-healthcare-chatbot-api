from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Client, UserClient
from app.schemas import UserRegister
from app.config import settings

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pre-hash to avoid bcrypt's 72-byte limit and normalize input
# This changes the effective secret used by bcrypt. If you had existing users
# hashed without pre-hashing, you'll need a migration strategy. For new projects
# it's safe to enable now.

def _bcrypt_safe_secret(password: str) -> bytes:
    """Pre-hash password with SHA256 before bcrypt to avoid 72-byte limit."""
    return hashlib.sha256(password.encode("utf-8")).digest()

def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    secret = _bcrypt_safe_secret(password)
    return pwd_context.hash(secret)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    secret = _bcrypt_safe_secret(plain_password)
    return pwd_context.verify(secret, hashed_password)

# --- User Creation ---
def create_user(db: Session, user_data: UserRegister):
    logger.info(f"Creating user: email={user_data.email}, client_code={user_data.client_code}")
    
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        logger.warning(f"Registration failed: Email already registered: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if client_code exists
    client = db.query(Client).filter(Client.client_code == user_data.client_code).first()
    if not client:
        logger.warning(f"Registration failed: Invalid client code: {user_data.client_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client code"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Link user to client
    user_client = UserClient(
        user_id=db_user.id,
        client_id=client.id,
        is_primary=1
    )
    db.add(user_client)
    db.commit()
    
    logger.info(f"User created successfully: {db_user.email}")
    return db_user

# --- JWT Token Handling ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer(auto_error=False)

logger.info(f"JWT configured with {ACCESS_TOKEN_EXPIRE_MINUTES} minute token expiry")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: Optional[str] = None

    # 1) Authorization: Bearer <token>
    if credentials and credentials.scheme and credentials.scheme.lower() == "bearer":
        cred = credentials.credentials
        if cred and cred not in ("null", "undefined"):
            token = cred

    # 2) X-Access-Token header
    if token is None:
        hat = request.headers.get("X-Access-Token")
        if hat and hat not in ("null", "undefined"):
            token = hat

    # 3) Cookie
    if token is None:
        cat = request.cookies.get("access_token")
        if cat and cat not in ("null", "undefined"):
            token = cat

    # 4) Query param
    if token is None:
        qat = request.query_params.get("access_token")
        if qat and qat not in ("null", "undefined"):
            token = qat

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise credentials_exception
    return user