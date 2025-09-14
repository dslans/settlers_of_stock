"""
Pydantic schemas for alert system.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ..models.alert import AlertType, AlertStatus


class NotificationSettings(BaseModel):
    """Notification preferences for alerts."""
    email: bool = True
    push: bool = True
    sms: bool = False


class AlertCondition(BaseModel):
    """Alert condition configuration."""
    type: AlertType
    value: Decimal = Field(..., description="Condition value (price, percentage, etc.)")
    operator: Optional[str] = Field(default=">=", description="Comparison operator")
    
    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['>', '<', '>=', '<=', '==', '!=']
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {valid_operators}')
        return v


class AlertCreate(BaseModel):
    """Schema for creating a new alert."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    alert_type: AlertType
    condition_value: Decimal = Field(..., description="Condition value")
    condition_operator: Optional[str] = Field(default=">=", description="Comparison operator")
    
    name: str = Field(..., min_length=1, max_length=255, description="Alert name")
    description: Optional[str] = Field(None, max_length=1000, description="Alert description")
    message_template: Optional[str] = Field(None, max_length=500, description="Custom message template")
    
    notification_settings: Optional[NotificationSettings] = None
    
    expires_at: Optional[datetime] = Field(None, description="Alert expiration time")
    max_triggers: Optional[int] = Field(default=1, ge=1, le=100, description="Maximum number of triggers")
    cooldown_minutes: Optional[int] = Field(default=60, ge=0, le=1440, description="Cooldown between triggers in minutes")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()
    
    @validator('condition_operator')
    def validate_operator(cls, v):
        if v is None:
            return ">="
        valid_operators = ['>', '<', '>=', '<=', '==', '!=']
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {valid_operators}')
        return v
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiration time must be in the future')
        return v


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    message_template: Optional[str] = Field(None, max_length=500)
    
    condition_value: Optional[Decimal] = None
    condition_operator: Optional[str] = None
    
    notification_settings: Optional[NotificationSettings] = None
    
    expires_at: Optional[datetime] = None
    max_triggers: Optional[int] = Field(None, ge=1, le=100)
    cooldown_minutes: Optional[int] = Field(None, ge=0, le=1440)
    
    @validator('condition_operator')
    def validate_operator(cls, v):
        if v is None:
            return v
        valid_operators = ['>', '<', '>=', '<=', '==', '!=']
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {valid_operators}')
        return v
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiration time must be in the future')
        return v


class AlertTriggerResponse(BaseModel):
    """Schema for alert trigger information."""
    id: int
    alert_id: int
    triggered_at: datetime
    trigger_value: Optional[Decimal]
    market_price: Optional[Decimal]
    message: Optional[str]
    
    email_sent: bool
    push_sent: bool
    sms_sent: bool
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: int
    user_id: int
    symbol: str
    alert_type: AlertType
    status: AlertStatus
    
    condition_value: Optional[Decimal]
    condition_operator: Optional[str]
    
    name: str
    description: Optional[str]
    message_template: Optional[str]
    
    notify_email: bool
    notify_push: bool
    notify_sms: bool
    
    expires_at: Optional[datetime]
    max_triggers: int
    trigger_count: int
    cooldown_minutes: int
    
    created_at: datetime
    updated_at: datetime
    last_checked_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    
    # Include recent triggers if requested
    triggers: Optional[List[AlertTriggerResponse]] = None
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Schema for paginated alert list."""
    alerts: List[AlertResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class AlertStatsResponse(BaseModel):
    """Schema for alert statistics."""
    total_alerts: int
    active_alerts: int
    paused_alerts: int
    triggered_alerts: int
    recent_triggers: List[Dict[str, Any]]


class AlertBulkCreateRequest(BaseModel):
    """Schema for creating multiple alerts."""
    alerts: List[AlertCreate] = Field(..., min_items=1, max_items=50)


class AlertBulkCreateResponse(BaseModel):
    """Schema for bulk alert creation response."""
    created_alerts: List[AlertResponse]
    failed_alerts: List[Dict[str, str]]
    total_created: int
    total_failed: int


class AlertTestRequest(BaseModel):
    """Schema for testing alert conditions."""
    alert_id: int
    force_trigger: bool = False


class AlertTestResponse(BaseModel):
    """Schema for alert test results."""
    alert_id: int
    symbol: str
    current_conditions: Dict[str, Any]
    would_trigger: bool
    trigger_reason: Optional[str]
    test_timestamp: datetime


class PriceAlertQuickCreate(BaseModel):
    """Schema for quickly creating price alerts."""
    symbol: str = Field(..., min_length=1, max_length=20)
    target_price: Decimal = Field(..., gt=0)
    alert_when: str = Field(..., pattern="^(above|below)$")
    name: Optional[str] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()
    
    @validator('name')
    def generate_name_if_empty(cls, v, values):
        if not v and 'symbol' in values and 'target_price' in values and 'alert_when' in values:
            symbol = values['symbol']
            price = values['target_price']
            direction = values['alert_when']
            return f"{symbol} {direction} ${price}"
        return v


class AlertNotificationTest(BaseModel):
    """Schema for testing notification delivery."""
    notification_types: List[str] = Field(default=["email", "push"], description="Types to test")
    
    @validator('notification_types')
    def validate_notification_types(cls, v):
        valid_types = ['email', 'push', 'sms', 'webhook']
        for notification_type in v:
            if notification_type not in valid_types:
                raise ValueError(f'Invalid notification type: {notification_type}. Valid types: {valid_types}')
        return v


class AlertNotificationTestResponse(BaseModel):
    """Schema for notification test results."""
    results: Dict[str, bool]
    timestamp: datetime
    message: str


# WebSocket message schemas for real-time alerts

class AlertWebSocketMessage(BaseModel):
    """Schema for WebSocket alert messages."""
    type: str = "alert_triggered"
    alert_id: int
    symbol: str
    message: str
    trigger_data: Dict[str, Any]
    timestamp: datetime


class AlertStatusUpdate(BaseModel):
    """Schema for alert status updates via WebSocket."""
    type: str = "alert_status_update"
    alert_id: int
    old_status: AlertStatus
    new_status: AlertStatus
    timestamp: datetime