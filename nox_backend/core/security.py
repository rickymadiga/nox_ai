"""
Security utilities for authentication, password hashing, and JWT handling
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from nox_backend.core.config import SECRET_KEY, ALGORITHM, DEV_USERS


# ============================================================================
# PASSWORD HASHING
# ============================================================================

SECRET_KEY = "erickisalili1ve"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def normalize_password(password: str) -> str:
    """Normalize password using SHA256 before hashing (extra layer)."""
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    """Hash password securely."""
    return pwd_context.hash(normalize_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        return pwd_context.verify(normalize_password(plain), hashed)
    except Exception:
        return False


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    
    payload = {
        "sub": username,
        "exp": expire
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ============================================================================
# FASTAPI DEPENDENCIES
# ============================================================================

def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract current user from token."""
    
    payload = verify_token(cred.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload.get("sub")


def require_admin(user: str = Depends(get_current_user)) -> str:
    """Ensure current user is admin."""
    
    if user not in DEV_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


# ============================================================================
# OPTIONAL HELPERS (USEFUL FOR FRONTEND / DEBUG)
# ============================================================================

def is_admin_user(username: str) -> bool:
    """Check if a username is admin."""
    return username in DEV_USERS


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get token expiry time."""
    payload = verify_token(token)
    if not payload:
        return None
    
    exp = payload.get("exp")
    if exp:
        return datetime.fromtimestamp(exp)
    
    return None


def decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")  # or "user_id"