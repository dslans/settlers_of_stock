"""
Alert models for price and condition-based notifications.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from ..core.database import Base

class AlertType(PyEnum):
    """Types of alerts that can be created."""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PERCENT = "price_change_percent"
    VOLUME_SPIKE = "volume_spike"
    TECHNICAL_BREAKOUT = "technical_breakout"
    TECHNICAL_BREAKDOWN = "technical_breakdown"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MOVING_AVERAGE_CROSS = "moving_average_cross"
    NEWS_SENTIMENT = "news_sentiment"
    EARNINGS_DATE = "earnings_date"
    ANALYST_UPGRADE = "analyst_upgrade"
    ANALYST_DOWNGRADE = "analyst_downgrade"

class AlertStatus(PyEnum):
    """Status of alert processing."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Alert(Base):
    """Alert model for stock notifications."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Alert configuration
    alert_type = Column(Enum(AlertType), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False)
    
    # Alert conditions (stored as JSON-like structure)
    condition_value = Column(Numeric(15, 4), nullable=True)  # Price, percentage, etc.
    condition_operator = Column(String(10), nullable=True)   # >, <, >=, <=, ==
    
    # Alert metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    message_template = Column(Text, nullable=True)
    
    # Notification settings
    notify_email = Column(Boolean, default=True, nullable=False)
    notify_push = Column(Boolean, default=True, nullable=False)
    notify_sms = Column(Boolean, default=False, nullable=False)
    
    # Expiration and frequency
    expires_at = Column(DateTime(timezone=True), nullable=True)
    max_triggers = Column(Integer, default=1, nullable=False)  # How many times to trigger
    trigger_count = Column(Integer, default=0, nullable=False)  # How many times triggered
    cooldown_minutes = Column(Integer, default=60, nullable=False)  # Cooldown between triggers
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    triggers = relationship("AlertTrigger", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, symbol='{self.symbol}', type='{self.alert_type}', status='{self.status}')>"

class AlertTrigger(Base):
    """Record of when alerts were triggered."""
    
    __tablename__ = "alert_triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    
    # Trigger details
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    trigger_value = Column(Numeric(15, 4), nullable=True)  # The value that triggered the alert
    market_price = Column(Numeric(10, 2), nullable=True)   # Stock price at trigger time
    
    # Notification status
    email_sent = Column(Boolean, default=False, nullable=False)
    push_sent = Column(Boolean, default=False, nullable=False)
    sms_sent = Column(Boolean, default=False, nullable=False)
    
    # Additional context
    message = Column(Text, nullable=True)
    trigger_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Relationships
    alert = relationship("Alert", back_populates="triggers")
    
    def __repr__(self):
        return f"<AlertTrigger(id={self.id}, alert_id={self.alert_id}, triggered_at='{self.triggered_at}')>"