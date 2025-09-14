"""
Authentication utilities for JWT token handling and password management.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import ValidationError

from .config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (usually user ID or email) to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        The subject (user identifier) if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = payload.get("sub")
        if token_data is None:
            return None
        return str(token_data)
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength according to security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements, False otherwise
        
    Raises:
        HTTPException: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    
    return True


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Create a refresh token with longer expiration.
    
    Args:
        subject: The subject to encode in the token
        
    Returns:
        Encoded refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify and decode a refresh token.
    
    Args:
        token: Refresh token string to verify
        
    Returns:
        The subject if token is valid and is a refresh token, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            return None
        token_data = payload.get("sub")
        if token_data is None:
            return None
        return str(token_data)
    except JWTError:
        return None