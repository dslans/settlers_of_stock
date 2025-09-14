"""
FastAPI dependencies for authentication and database access.
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from .database import get_db
from .auth import verify_token
from ..models.user import User

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate JWT token from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Valid JWT token string
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


async def get_current_user_email(
    token: str = Depends(get_current_user_token)
) -> str:
    """
    Extract user email from JWT token.
    
    Args:
        token: Valid JWT token
        
    Returns:
        User email from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        email = verify_token(token)
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception


async def get_current_user(
    db: Session = Depends(get_db),
    email: str = Depends(get_current_user_email)
) -> User:
    """
    Get current authenticated user from database.
    
    Args:
        db: Database session
        email: User email from JWT token
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If user not found or inactive
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user for clarity).
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active user object
    """
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current verified user (requires email verification).
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current verified user object
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    
    Args:
        db: Database session
        credentials: Optional HTTP authorization credentials
        
    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        email = verify_token(token)
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None