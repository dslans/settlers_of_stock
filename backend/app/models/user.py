"""
User model for authentication and user management.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class User(Base):
    """User model for authentication and preferences."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # User preferences stored as JSON
    preferences = Column(JSON, nullable=True, default={
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
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_active = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    learning_progress = relationship("UserLearningProgress", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"