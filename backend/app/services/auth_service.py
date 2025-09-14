"""
Authentication service for user management and authentication operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User
from ..schemas.auth import UserCreate, UserUpdate, UserUpdatePassword
from ..core.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    validate_password_strength
)


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if user already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        validate_password_strength(user_data.password)
        
        # Create user with hashed password
        hashed_password = get_password_hash(user_data.password)
        
        # Set default preferences if not provided
        preferences = user_data.preferences.dict() if user_data.preferences else {
            "risk_tolerance": "moderate",
            "investment_horizon": "medium",
            "preferred_analysis": ["fundamental", "technical"],
            "notification_settings": {
                "email_alerts": True,
                "push_notifications": True,
                "price_alerts": True,
                "news_alerts": False
            },
            "display_settings": {
                "theme": "light",
                "currency": "USD",
                "chart_type": "candlestick"
            }
        }
        
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            preferences=preferences,
            is_active=True,
            is_verified=False  # Require email verification
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last active timestamp
        user.last_active = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def update_user(self, user: User, user_data: UserUpdate) -> User:
        """
        Update user information.
        
        Args:
            user: User object to update
            user_data: Updated user data
            
        Returns:
            Updated user object
        """
        update_data = user_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "preferences" and value:
                # Merge with existing preferences
                existing_prefs = user.preferences or {}
                if isinstance(value, dict):
                    existing_prefs.update(value)
                else:
                    existing_prefs.update(value.dict())
                setattr(user, field, existing_prefs)
            else:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user_password(self, user: User, password_data: UserUpdatePassword) -> User:
        """
        Update user password.
        
        Args:
            user: User object to update
            password_data: Password update data
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If current password is incorrect or validation fails
        """
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        validate_password_strength(password_data.new_password)
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user: User) -> User:
        """
        Deactivate user account.
        
        Args:
            user: User object to deactivate
            
        Returns:
            Updated user object
        """
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def verify_user_email(self, user: User) -> User:
        """
        Mark user email as verified.
        
        Args:
            user: User object to verify
            
        Returns:
            Updated user object
        """
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def create_tokens(self, user: User) -> Dict[str, Any]:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: User object to create tokens for
            
        Returns:
            Dictionary containing access_token, refresh_token, token_type, and expires_in
        """
        access_token = create_access_token(subject=user.email)
        refresh_token = create_refresh_token(subject=user.email)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 minutes in seconds
        }
    
    def refresh_access_token(self, user: User) -> Dict[str, Any]:
        """
        Create new access token for user.
        
        Args:
            user: User object to create token for
            
        Returns:
            Dictionary containing new access_token, token_type, and expires_in
        """
        access_token = create_access_token(subject=user.email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 minutes in seconds
        }