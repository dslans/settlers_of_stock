"""
Watchlist schemas for request/response validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal


class WatchlistItemBase(BaseModel):
    """Base watchlist item schema."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    notes: Optional[str] = Field(None, max_length=1000, description="User notes about the stock")
    target_price: Optional[Decimal] = Field(None, ge=0, description="Target price for the stock")
    entry_price: Optional[Decimal] = Field(None, ge=0, description="Entry price if owned")
    shares_owned: Optional[Decimal] = Field(None, ge=0, description="Number of shares owned")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v:
            v = v.upper().strip()
            if not v.replace('.', '').replace('-', '').isalnum():
                raise ValueError('Symbol must contain only letters, numbers, dots, and hyphens')
        return v


class WatchlistItemCreate(WatchlistItemBase):
    """Schema for creating a watchlist item."""
    pass


class WatchlistItemUpdate(BaseModel):
    """Schema for updating a watchlist item."""
    company_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)
    target_price: Optional[Decimal] = Field(None, ge=0)
    entry_price: Optional[Decimal] = Field(None, ge=0)
    shares_owned: Optional[Decimal] = Field(None, ge=0)


class WatchlistItemResponse(WatchlistItemBase):
    """Schema for watchlist item response."""
    id: int
    watchlist_id: int
    added_at: datetime
    updated_at: datetime
    
    # Real-time market data (populated dynamically)
    current_price: Optional[Decimal] = None
    daily_change: Optional[Decimal] = None
    daily_change_percent: Optional[Decimal] = None
    volume: Optional[int] = None
    is_market_open: Optional[bool] = None
    last_updated: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class WatchlistBase(BaseModel):
    """Base watchlist schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Watchlist name")
    description: Optional[str] = Field(None, max_length=1000, description="Watchlist description")
    is_default: bool = Field(False, description="Whether this is the default watchlist")


class WatchlistCreate(WatchlistBase):
    """Schema for creating a watchlist."""
    pass


class WatchlistUpdate(BaseModel):
    """Schema for updating a watchlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_default: Optional[bool] = None


class WatchlistResponse(WatchlistBase):
    """Schema for watchlist response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[WatchlistItemResponse] = []
    
    # Summary statistics (populated dynamically)
    total_items: int = 0
    total_value: Optional[Decimal] = None
    total_gain_loss: Optional[Decimal] = None
    total_gain_loss_percent: Optional[Decimal] = None
    
    model_config = {"from_attributes": True}


class WatchlistSummary(BaseModel):
    """Schema for watchlist summary (without items)."""
    id: int
    name: str
    description: Optional[str]
    is_default: bool
    user_id: int
    created_at: datetime
    updated_at: datetime
    total_items: int = 0
    
    model_config = {"from_attributes": True}


class WatchlistBulkAddRequest(BaseModel):
    """Schema for adding multiple stocks to a watchlist."""
    symbols: List[str] = Field(..., min_items=1, max_items=50, description="List of stock symbols to add")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        # Clean and validate symbols
        cleaned_symbols = []
        for symbol in v:
            if symbol:
                symbol = symbol.upper().strip()
                if symbol.replace('.', '').replace('-', '').isalnum():
                    cleaned_symbols.append(symbol)
        
        if not cleaned_symbols:
            raise ValueError('At least one valid symbol is required')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in cleaned_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        return unique_symbols


class WatchlistBulkAddResponse(BaseModel):
    """Schema for bulk add response."""
    added_symbols: List[str] = []
    failed_symbols: List[dict] = []  # [{"symbol": "XYZ", "error": "Invalid symbol"}]
    total_added: int = 0
    total_failed: int = 0


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str
    success: bool = True


class WatchlistStatsResponse(BaseModel):
    """Schema for watchlist statistics."""
    total_watchlists: int
    total_items: int
    most_watched_symbols: List[dict]  # [{"symbol": "AAPL", "count": 5}]
    recent_additions: List[str]
    performance_summary: dict