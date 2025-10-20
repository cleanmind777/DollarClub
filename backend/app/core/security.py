from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import HTTPException, status
import bcrypt
import hashlib
import base64
from .config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _normalize_password(password: str) -> bytes:
    """
    Normalize password to handle bcrypt's 72-byte limit.
    For passwords longer than 72 bytes, we pre-hash with SHA256.
    Returns bytes suitable for bcrypt.
    """
    password_bytes = password.encode('utf-8')
    # bcrypt has a 72-byte limit, so we pre-hash long passwords
    if len(password_bytes) > 72:
        # Hash with SHA256 to reduce length
        return hashlib.sha256(password_bytes).digest()
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        normalized = _normalize_password(plain_password)
        return bcrypt.checkpw(normalized, hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt"""
    normalized = _normalize_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(normalized, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user_id(token: str) -> Optional[int]:
    """Extract user ID from JWT token"""
    payload = verify_token(token)
    if payload is None:
        return None
    return payload.get("sub")
