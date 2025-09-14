"""
Authentication API endpoints for user registration, login, and profile management.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import (
    get_current_user, 
    get_current_active_user,
    get_current_verified_user
)
from ..core.auth import verify_refresh_token
from ..services.auth_service import AuthService
from ..schemas.auth import (
    UserCreate,
    UserUpdate,
    UserUpdatePassword,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
    AuthResponse,
    LogoutResponse,
    MessageResponse
)
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user account.
    
    Creates a new user with the provided information and returns
    authentication tokens for immediate login.
    """
    auth_service = AuthService(db)
    
    try:
        # Create user
        user = auth_service.create_user(user_data)
        
        # Create tokens
        tokens = auth_service.create_tokens(user)
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            token=Token(**tokens),
            message="User registered successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate user and return access tokens.
    
    Validates user credentials and returns JWT tokens for API access.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = auth_service.create_tokens(user)
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=Token(**tokens),
        message="Login successful"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    
    Validates refresh token and returns a new access token.
    """
    # Verify refresh token
    email = verify_refresh_token(refresh_data.refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    token_data = auth_service.refresh_access_token(user)
    
    return Token(**token_data)


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user.
    
    Note: With JWT tokens, logout is primarily handled client-side
    by removing the token. This endpoint is for consistency and
    potential future server-side token blacklisting.
    """
    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user profile information.
    
    Returns the authenticated user's profile data.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user profile information.
    
    Updates the authenticated user's profile with the provided data.
    """
    auth_service = AuthService(db)
    
    try:
        updated_user = auth_service.update_user(current_user, user_update)
        return UserResponse.model_validate(updated_user)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.put("/me/password", response_model=MessageResponse)
async def update_current_user_password(
    password_update: UserUpdatePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user password.
    
    Updates the authenticated user's password after verifying the current password.
    """
    auth_service = AuthService(db)
    
    try:
        auth_service.update_user_password(current_user, password_update)
        return MessageResponse(message="Password updated successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )


@router.delete("/me", response_model=MessageResponse)
async def deactivate_current_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Deactivate current user account.
    
    Deactivates the authenticated user's account. The account can be
    reactivated by contacting support.
    """
    auth_service = AuthService(db)
    
    try:
        auth_service.deactivate_user(current_user)
        return MessageResponse(message="Account deactivated successfully")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


@router.get("/verify-token", response_model=UserResponse)
async def verify_current_token(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Verify current authentication token.
    
    Returns user information if the token is valid, otherwise returns 401.
    Useful for client-side token validation.
    """
    return UserResponse.model_validate(current_user)


@router.get("/preferences", response_model=dict)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user preferences.
    
    Returns the authenticated user's preferences and settings.
    """
    return current_user.preferences or {}


@router.put("/preferences", response_model=dict)
async def update_user_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user preferences.
    
    Updates the authenticated user's preferences and settings.
    """
    auth_service = AuthService(db)
    
    try:
        # Merge with existing preferences
        existing_prefs = current_user.preferences or {}
        existing_prefs.update(preferences)
        
        user_update = UserUpdate(preferences=existing_prefs)
        updated_user = auth_service.update_user(current_user, user_update)
        
        return updated_user.preferences or {}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )