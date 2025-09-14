"""
Stock data models using Pydantic for validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class Stock(BaseModel):
    """Core stock information model."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    exchange: str = Field(..., min_length=1, max_length=50, description="Stock exchange")
    sector: Optional[str] = Field(None, max_length=100, description="Business sector")
    industry: Optional[str] = Field(None, max_length=100, description="Industry classification")
    market_cap: Optional[int] = Field(None, ge=0, description="Market capitalization in USD")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        if not v.isalpha() and '.' not in v:
            raise ValueError('Stock symbol must contain only letters or include a dot for international stocks')
        return v.upper()
    
    @validator('market_cap')
    def validate_market_cap(cls, v):
        """Validate market cap is reasonable."""
        if v is not None and v < 0:
            raise ValueError('Market cap cannot be negative')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "market_cap": 3000000000000,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }


class MarketData(BaseModel):
    """Real-time market data model."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    price: Decimal = Field(..., ge=0, description="Current stock price")
    change: Decimal = Field(..., description="Price change from previous close")
    change_percent: Decimal = Field(..., description="Percentage change from previous close")
    volume: int = Field(..., ge=0, description="Trading volume")
    high_52_week: Optional[Decimal] = Field(None, ge=0, description="52-week high price")
    low_52_week: Optional[Decimal] = Field(None, ge=0, description="52-week low price")
    avg_volume: Optional[int] = Field(None, ge=0, description="Average trading volume")
    market_cap: Optional[int] = Field(None, ge=0, description="Current market capitalization")
    pe_ratio: Optional[Decimal] = Field(None, description="Price-to-earnings ratio")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")
    is_stale: bool = Field(default=False, description="Whether data is from cache/stale")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        return v.upper()
    
    @validator('price', 'high_52_week', 'low_52_week')
    def validate_positive_prices(cls, v):
        """Validate prices are positive."""
        if v is not None and v < 0:
            raise ValueError('Prices cannot be negative')
        return v
    
    @validator('change_percent')
    def validate_change_percent(cls, v):
        """Validate change percent is reasonable."""
        if v < -100:
            raise ValueError('Change percent cannot be less than -100%')
        return v
    
    @classmethod
    def from_yfinance(cls, yf_data: Dict[str, Any]) -> 'MarketData':
        """Create MarketData from yfinance ticker info."""
        # Handle both currentPrice and regularMarketPrice fields
        price = yf_data.get('currentPrice') or yf_data.get('regularMarketPrice', 0)
        
        return cls(
            symbol=yf_data.get('symbol', ''),
            price=Decimal(str(price)),
            change=Decimal(str(yf_data.get('regularMarketChange', 0))),
            change_percent=Decimal(str(yf_data.get('regularMarketChangePercent', 0))),
            volume=yf_data.get('volume', 0),
            high_52_week=Decimal(str(yf_data.get('fiftyTwoWeekHigh', 0))) if yf_data.get('fiftyTwoWeekHigh') else None,
            low_52_week=Decimal(str(yf_data.get('fiftyTwoWeekLow', 0))) if yf_data.get('fiftyTwoWeekLow') else None,
            avg_volume=yf_data.get('averageVolume'),
            market_cap=yf_data.get('marketCap'),
            pe_ratio=Decimal(str(yf_data.get('trailingPE', 0))) if yf_data.get('trailingPE') else None,
            timestamp=datetime.now()
        )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "price": 150.25,
                "change": 2.50,
                "change_percent": 1.69,
                "volume": 75000000,
                "high_52_week": 180.00,
                "low_52_week": 120.00,
                "avg_volume": 80000000,
                "market_cap": 2500000000000,
                "pe_ratio": 25.5,
                "timestamp": "2024-01-15T15:30:00Z",
                "is_stale": False
            }
        }