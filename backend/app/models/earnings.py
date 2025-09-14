"""
Earnings calendar and corporate events data models.
"""

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from ..core.database import Base


class EventType(str, Enum):
    """Types of corporate events."""
    EARNINGS = "earnings"
    DIVIDEND = "dividend"
    STOCK_SPLIT = "stock_split"
    MERGER = "merger"
    ACQUISITION = "acquisition"
    SPINOFF = "spinoff"
    RIGHTS_OFFERING = "rights_offering"
    SPECIAL_DIVIDEND = "special_dividend"
    CONFERENCE_CALL = "conference_call"
    ANALYST_DAY = "analyst_day"


class EarningsConfidence(str, Enum):
    """Confidence levels for earnings estimates."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCONFIRMED = "unconfirmed"


class EventImpact(str, Enum):
    """Expected impact levels for events."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


# SQLAlchemy Models for Database Storage

class EarningsEvent(Base):
    """Database model for earnings events."""
    __tablename__ = "earnings_events"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    
    # Event timing
    earnings_date = Column(DateTime, nullable=False, index=True)
    report_time = Column(String(20))  # "BMO" (before market open), "AMC" (after market close), "DMT" (during market)
    fiscal_quarter = Column(String(10))  # Q1, Q2, Q3, Q4
    fiscal_year = Column(Integer)
    
    # Estimates
    eps_estimate = Column(Numeric(10, 4))
    eps_estimate_high = Column(Numeric(10, 4))
    eps_estimate_low = Column(Numeric(10, 4))
    eps_estimate_count = Column(Integer)  # Number of analysts
    revenue_estimate = Column(Numeric(15, 2))
    revenue_estimate_high = Column(Numeric(15, 2))
    revenue_estimate_low = Column(Numeric(15, 2))
    
    # Actuals (filled after earnings are reported)
    eps_actual = Column(Numeric(10, 4))
    revenue_actual = Column(Numeric(15, 2))
    eps_surprise = Column(Numeric(10, 4))  # actual - estimate
    revenue_surprise = Column(Numeric(15, 2))
    
    # Metadata
    confidence = Column(SQLEnum(EarningsConfidence), default=EarningsConfidence.MEDIUM)
    impact_level = Column(SQLEnum(EventImpact), default=EventImpact.MEDIUM)
    is_confirmed = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    historical_performance = relationship("EarningsHistoricalPerformance", back_populates="earnings_event")


class CorporateEvent(Base):
    """Database model for corporate events (dividends, splits, etc.)."""
    __tablename__ = "corporate_events"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    
    # Event details
    event_type = Column(SQLEnum(EventType), nullable=False)
    event_date = Column(DateTime, nullable=False, index=True)
    ex_date = Column(DateTime)  # Ex-dividend date
    record_date = Column(DateTime)  # Record date
    payment_date = Column(DateTime)  # Payment date
    
    # Event-specific data
    dividend_amount = Column(Numeric(10, 4))  # For dividend events
    split_ratio = Column(String(20))  # For stock splits (e.g., "2:1", "3:2")
    split_factor = Column(Numeric(10, 6))  # Numerical split factor
    
    # Description and impact
    description = Column(Text)
    impact_level = Column(SQLEnum(EventImpact), default=EventImpact.MEDIUM)
    is_confirmed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EarningsHistoricalPerformance(Base):
    """Historical earnings performance and patterns."""
    __tablename__ = "earnings_historical_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    earnings_event_id = Column(Integer, ForeignKey("earnings_events.id"))
    symbol = Column(String(10), nullable=False, index=True)
    
    # Performance metrics
    price_before_earnings = Column(Numeric(10, 2))  # Price 1 day before
    price_after_earnings = Column(Numeric(10, 2))   # Price 1 day after
    price_change_1d = Column(Numeric(10, 4))        # 1-day change %
    price_change_1w = Column(Numeric(10, 4))        # 1-week change %
    price_change_1m = Column(Numeric(10, 4))        # 1-month change %
    
    volume_before = Column(Integer)
    volume_after = Column(Integer)
    volume_change = Column(Numeric(10, 4))  # Volume change %
    
    # Beat/miss patterns
    beat_estimate = Column(Boolean)  # Did it beat EPS estimate?
    surprise_magnitude = Column(Numeric(10, 4))  # How much it beat/missed by
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    earnings_event = relationship("EarningsEvent", back_populates="historical_performance")


# Pydantic Models for API

class EarningsEventBase(BaseModel):
    """Base earnings event model."""
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1, max_length=200)
    earnings_date: datetime
    report_time: Optional[str] = Field(None, pattern="^(BMO|AMC|DMT)$")
    fiscal_quarter: Optional[str] = Field(None, pattern="^Q[1-4]$")
    fiscal_year: Optional[int] = Field(None, ge=2000, le=2100)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()


class EarningsEstimates(BaseModel):
    """Earnings estimates model."""
    eps_estimate: Optional[Decimal] = None
    eps_estimate_high: Optional[Decimal] = None
    eps_estimate_low: Optional[Decimal] = None
    eps_estimate_count: Optional[int] = Field(None, ge=0)
    revenue_estimate: Optional[Decimal] = None
    revenue_estimate_high: Optional[Decimal] = None
    revenue_estimate_low: Optional[Decimal] = None


class EarningsActuals(BaseModel):
    """Actual earnings results model."""
    eps_actual: Optional[Decimal] = None
    revenue_actual: Optional[Decimal] = None
    eps_surprise: Optional[Decimal] = None
    revenue_surprise: Optional[Decimal] = None


class EarningsEventCreate(EarningsEventBase, EarningsEstimates):
    """Model for creating earnings events."""
    confidence: EarningsConfidence = EarningsConfidence.MEDIUM
    impact_level: EventImpact = EventImpact.MEDIUM
    is_confirmed: bool = False
    notes: Optional[str] = None


class EarningsEventUpdate(BaseModel):
    """Model for updating earnings events."""
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


class EarningsEventResponse(EarningsEventBase, EarningsEstimates, EarningsActuals):
    """Complete earnings event response model."""
    id: int
    confidence: EarningsConfidence
    impact_level: EventImpact
    is_confirmed: bool
    notes: Optional[str] = None
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
            Decimal: lambda v: float(v)
        }


class CorporateEventBase(BaseModel):
    """Base corporate event model."""
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1, max_length=200)
    event_type: EventType
    event_date: datetime
    description: Optional[str] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()


class CorporateEventCreate(CorporateEventBase):
    """Model for creating corporate events."""
    ex_date: Optional[datetime] = None
    record_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    dividend_amount: Optional[Decimal] = Field(None, ge=0)
    split_ratio: Optional[str] = None
    split_factor: Optional[Decimal] = Field(None, gt=0)
    impact_level: EventImpact = EventImpact.MEDIUM
    is_confirmed: bool = False


class CorporateEventResponse(CorporateEventBase):
    """Corporate event response model."""
    id: int
    ex_date: Optional[datetime] = None
    record_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    dividend_amount: Optional[Decimal] = None
    split_ratio: Optional[str] = None
    split_factor: Optional[Decimal] = None
    impact_level: EventImpact
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    days_until_event: Optional[int] = None
    is_upcoming: bool = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class EarningsHistoricalPerformanceResponse(BaseModel):
    """Historical earnings performance response model."""
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
            Decimal: lambda v: float(v)
        }


class EarningsCalendarFilter(BaseModel):
    """Filter model for earnings calendar queries."""
    symbols: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    confirmed_only: bool = False
    impact_levels: Optional[List[EventImpact]] = None
    has_estimates: Optional[bool] = None
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if v:
            return [symbol.upper() for symbol in v]
        return v


class EventCalendarFilter(BaseModel):
    """Filter model for corporate events calendar queries."""
    symbols: Optional[List[str]] = None
    event_types: Optional[List[EventType]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    confirmed_only: bool = False
    impact_levels: Optional[List[EventImpact]] = None
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if v:
            return [symbol.upper() for symbol in v]
        return v


class EarningsCalendarResponse(BaseModel):
    """Response model for earnings calendar."""
    total_events: int
    upcoming_events: int
    events: List[EarningsEventResponse]
    date_range: Dict[str, Optional[date]]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class EventCalendarResponse(BaseModel):
    """Response model for corporate events calendar."""
    total_events: int
    upcoming_events: int
    events: List[CorporateEventResponse]
    date_range: Dict[str, Optional[date]]
    event_types: List[EventType]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class EarningsImpactAnalysis(BaseModel):
    """Analysis of earnings impact on stock price."""
    symbol: str
    upcoming_earnings: Optional[EarningsEventResponse] = None
    historical_performance: List[EarningsHistoricalPerformanceResponse]
    
    # Analysis metrics
    avg_price_change_1d: Optional[Decimal] = None
    avg_price_change_1w: Optional[Decimal] = None
    avg_volume_change: Optional[Decimal] = None
    beat_rate: Optional[Decimal] = None  # Percentage of times beat estimates
    volatility_increase: Optional[Decimal] = None
    
    # Predictions
    expected_volatility: Optional[str] = None  # "high", "medium", "low"
    risk_level: Optional[str] = None
    key_metrics_to_watch: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }