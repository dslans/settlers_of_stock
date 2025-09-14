"""
Authentication schemas for request/response validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime


class UserPreferences(BaseModel):
    """User preferences schema."""
    risk_tolerance: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    investment_horizon: str = Field(default="medium", pattern="^(short|medium|long)$")
    preferred_analysis: List[str] = Field(default=["fundamental", "technical"])
    notification_settings: Dict[str, bool] = Field(default={
        "email_alerts": True,
        "push_notifications": True,
        "price_alerts": True,
        "news_alerts": False
    })
    display_settings: Dict[str, str] = Field(default={
        "theme": "light",
        "currency": "USD",
        "chart_type": "candlestick"
    })
    
    @validator('preferred_analysis')
    def validate_analysis_types(cls, v):
        valid_types = {"fundamental", "technical", "sentiment"}
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(f"Invalid analysis type: {analysis_type}")
        return v


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class UserUpdatePassword(BaseModel):
    """Schema for password updates."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_active: datetime
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for token payload data."""
    email: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""
    email: EmailStr


class EmailVerification(BaseModel):
    """Schema for email verification with token."""
    token: str


class AuthResponse(BaseModel):
    """Schema for authentication response."""
    user: UserResponse
    token: Token
    message: str = "Authentication successful"


class LogoutResponse(BaseModel):
    """Schema for logout response."""
    message: str = "Logged out successfully"


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str
    success: bool = True