"""
Pydantic schemas for earnings calendar and corporate events API.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from ..models.earnings import EventType, EarningsConfidence, EventImpact


class EarningsEventSchema(BaseModel):
    """Schema for earnings event data."""
    
    id: int
    symbol: str
    company_name: str
    earnings_date: datetime
    report_time: Optional[str] = None
    fiscal_quarter: Optional[str] = None
    fiscal_year: Optional[int] = None
    
    # Estimates
    eps_estimate: Optional[Decimal] = None
    eps_estimate_high: Optional[Decimal] = None
    eps_estimate_low: Optional[Decimal] = None
    eps_estimate_count: Optional[int] = None
    revenue_estimate: Optional[Decimal] = None
    revenue_estimate_high: Optional[Decimal] = None
    revenue_estimate_low: Optional[Decimal] = None
    
    # Actuals
    eps_actual: Optional[Decimal] = None
    revenue_actual: Optional[Decimal] = None
    eps_surprise: Optional[Decimal] = None
    revenue_surprise: Optional[Decimal] = None
    
    # Metadata
    confidence: EarningsConfidence
    impact_level: EventImpact
    is_confirmed: bool
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    days_until_earnings: Optional[int] = None
    is_upcoming: bool = False
    has_estimates: bool = False
    has_actuals: bool = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }


class CorporateEventSchema(BaseModel):
    """Schema for corporate event data."""
    
    id: int
    symbol: str
    company_name: str
    event_type: EventType
    event_date: datetime
    ex_date: Optional[datetime] = None
    record_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    
    # Event-specific data
    dividend_amount: Optional[Decimal] = None
    split_ratio: Optional[str] = None
    split_factor: Optional[Decimal] = None
    
    # Description and impact
    description: Optional[str] = None
    impact_level: EventImpact
    is_confirmed: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    days_until_event: Optional[int] = None
    is_upcoming: bool = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }


class EarningsHistoricalPerformanceSchema(BaseModel):
    """Schema for historical earnings performance data."""
    
    id: int
    symbol: str
    price_before_earnings: Optional[Decimal] = None
    price_after_earnings: Optional[Decimal] = None
    price_change_1d: Optional[Decimal] = None
    price_change_1w: Optional[Decimal] = None
    price_change_1m: Optional[Decimal] = None
    volume_before: Optional[int] = None
    volume_after: Optional[int] = None
    volume_change: Optional[Decimal] = None
    beat_estimate: Optional[bool] = None
    surprise_magnitude: Optional[Decimal] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }


class EarningsCalendarRequestSchema(BaseModel):
    """Schema for earnings calendar request parameters."""
    
    symbols: Optional[List[str]] = Field(None, description="List of stock symbols to filter")
    start_date: Optional[date] = Field(None, description="Start date for earnings events")
    end_date: Optional[date] = Field(None, description="End date for earnings events")
    confirmed_only: bool = Field(False, description="Only return confirmed earnings events")
    impact_levels: Optional[List[EventImpact]] = Field(None, description="Filter by impact levels")
    has_estimates: Optional[bool] = Field(None, description="Filter by whether events have estimates")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of events to return")
    offset: int = Field(0, ge=0, description="Number of events to skip")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if v:
            return [symbol.upper().strip() for symbol in v if symbol.strip()]
        return v


class CorporateEventsRequestSchema(BaseModel):
    """Schema for corporate events request parameters."""
    
    symbols: Optional[List[str]] = Field(None, description="List of stock symbols to filter")
    event_types: Optional[List[EventType]] = Field(None, description="Filter by event types")
    start_date: Optional[date] = Field(None, description="Start date for events")
    end_date: Optional[date] = Field(None, description="End date for events")
    confirmed_only: bool = Field(False, description="Only return confirmed events")
    impact_levels: Optional[List[EventImpact]] = Field(None, description="Filter by impact levels")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of events to return")
    offset: int = Field(0, ge=0, description="Number of events to skip")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if v:
            return [symbol.upper().strip() for symbol in v if symbol.strip()]
        return v


class EarningsCalendarResponseSchema(BaseModel):
    """Schema for earnings calendar response."""
    
    total_events: int
    upcoming_events: int
    events: List[EarningsEventSchema]
    date_range: Dict[str, Optional[date]]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }


class CorporateEventsResponseSchema(BaseModel):
    """Schema for corporate events response."""
    
    total_events: int
    upcoming_events: int
    events: List[CorporateEventSchema]
    date_range: Dict[str, Optional[date]]
    event_types: List[EventType]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }


class EarningsImpactAnalysisSchema(BaseModel):
    """Schema for earnings impact analysis."""
    
    symbol: str
    upcoming_earnings: Optional[EarningsEventSchema] = None
    historical_performance: List[EarningsHistoricalPerformanceSchema]
    
    # Analysis metrics
    avg_price_change_1d: Optional[Decimal] = None
    avg_price_change_1w: Optional[Decimal] = None
    avg_volume_change: Optional[Decimal] = None
    beat_rate: Optional[Decimal] = None
    volatility_increase: Optional[Decimal] = None
    
    # Predictions
    expected_volatility: Optional[str] = None
    risk_level: Optional[str] = None
    key_metrics_to_watch: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }


class FetchDataRequestSchema(BaseModel):
    """Schema for fetch data request."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    days_ahead: int = Field(90, ge=1, le=365, description="Number of days ahead to fetch data")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class FetchDataResponseSchema(BaseModel):
    """Schema for fetch data response."""
    
    message: str
    earnings_events_count: int
    corporate_events_count: int
    earnings_events: List[EarningsEventSchema]
    corporate_events: List[CorporateEventSchema]


class EarningsEventCreateSchema(BaseModel):
    """Schema for creating earnings events."""
    
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1, max_length=200)
    earnings_date: datetime
    report_time: Optional[str] = Field(None, pattern="^(BMO|AMC|DMT)$")
    fiscal_quarter: Optional[str] = Field(None, pattern="^Q[1-4]$")
    fiscal_year: Optional[int] = Field(None, ge=2000, le=2100)
    
    # Estimates
    eps_estimate: Optional[Decimal] = None
    eps_estimate_high: Optional[Decimal] = None
    eps_estimate_low: Optional[Decimal] = None
    eps_estimate_count: Optional[int] = Field(None, ge=0)
    revenue_estimate: Optional[Decimal] = None
    revenue_estimate_high: Optional[Decimal] = None
    revenue_estimate_low: Optional[Decimal] = None
    
    # Metadata
    confidence: EarningsConfidence = EarningsConfidence.MEDIUM
    impact_level: EventImpact = EventImpact.MEDIUM
    is_confirmed: bool = False
    notes: Optional[str] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class EarningsEventUpdateSchema(BaseModel):
    """Schema for updating earnings events."""
    
    earnings_date: Optional[datetime] = None
    report_time: Optional[str] = Field(None, pattern="^(BMO|AMC|DMT)$")
    eps_estimate: Optional[Decimal] = None
    revenue_estimate: Optional[Decimal] = None
    eps_actual: Optional[Decimal] = None
    revenue_actual: Optional[Decimal] = None
    confidence: Optional[EarningsConfidence] = None
    impact_level: Optional[EventImpact] = None
    is_confirmed: Optional[bool] = None
    notes: Optional[str] = None


class CorporateEventCreateSchema(BaseModel):
    """Schema for creating corporate events."""
    
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1, max_length=200)
    event_type: EventType
    event_date: datetime
    ex_date: Optional[datetime] = None
    record_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    
    # Event-specific data
    dividend_amount: Optional[Decimal] = Field(None, ge=0)
    split_ratio: Optional[str] = None
    split_factor: Optional[Decimal] = Field(None, gt=0)
    
    # Description and impact
    description: Optional[str] = None
    impact_level: EventImpact = EventImpact.MEDIUM
    is_confirmed: bool = False
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    
    message: str
    error_type: str
    suggestions: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Failed to fetch earnings data",
                "error_type": "DATA_FETCH_ERROR",
                "suggestions": ["Verify symbol exists", "Try again later"]
            }
        }