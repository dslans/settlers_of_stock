"""
Investment opportunity search models using Pydantic for validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum


class MarketCapCategory(str, Enum):
    """Market capitalization categories."""
    MEGA_CAP = "mega_cap"      # > $200B
    LARGE_CAP = "large_cap"    # $10B - $200B
    MID_CAP = "mid_cap"        # $2B - $10B
    SMALL_CAP = "small_cap"    # $300M - $2B
    MICRO_CAP = "micro_cap"    # < $300M


class OpportunityType(str, Enum):
    """Types of investment opportunities."""
    UNDERVALUED = "undervalued"
    GROWTH = "growth"
    MOMENTUM = "momentum"
    DIVIDEND = "dividend"
    BREAKOUT = "breakout"
    OVERSOLD = "oversold"
    EARNINGS_SURPRISE = "earnings_surprise"


class RiskLevel(str, Enum):
    """Risk levels for opportunities."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class OpportunitySearchFilters(BaseModel):
    """Filters for opportunity search."""
    
    # Market cap filters
    market_cap_min: Optional[int] = Field(None, ge=0, description="Minimum market cap in USD")
    market_cap_max: Optional[int] = Field(None, ge=0, description="Maximum market cap in USD")
    market_cap_categories: Optional[List[MarketCapCategory]] = Field(None, description="Market cap categories")
    
    # Sector and industry filters
    sectors: Optional[List[str]] = Field(None, description="Sectors to include")
    industries: Optional[List[str]] = Field(None, description="Industries to include")
    exclude_sectors: Optional[List[str]] = Field(None, description="Sectors to exclude")
    
    # Performance filters
    price_change_1d_min: Optional[Decimal] = Field(None, description="Minimum 1-day price change %")
    price_change_1d_max: Optional[Decimal] = Field(None, description="Maximum 1-day price change %")
    price_change_1w_min: Optional[Decimal] = Field(None, description="Minimum 1-week price change %")
    price_change_1w_max: Optional[Decimal] = Field(None, description="Maximum 1-week price change %")
    price_change_1m_min: Optional[Decimal] = Field(None, description="Minimum 1-month price change %")
    price_change_1m_max: Optional[Decimal] = Field(None, description="Maximum 1-month price change %")
    
    # Volume filters
    volume_min: Optional[int] = Field(None, ge=0, description="Minimum daily volume")
    avg_volume_min: Optional[int] = Field(None, ge=0, description="Minimum average volume")
    
    # Fundamental filters
    pe_ratio_min: Optional[Decimal] = Field(None, description="Minimum P/E ratio")
    pe_ratio_max: Optional[Decimal] = Field(None, description="Maximum P/E ratio")
    pb_ratio_min: Optional[Decimal] = Field(None, description="Minimum P/B ratio")
    pb_ratio_max: Optional[Decimal] = Field(None, description="Maximum P/B ratio")
    roe_min: Optional[Decimal] = Field(None, description="Minimum ROE")
    debt_to_equity_max: Optional[Decimal] = Field(None, description="Maximum debt-to-equity ratio")
    profit_margin_min: Optional[Decimal] = Field(None, description="Minimum profit margin")
    revenue_growth_min: Optional[Decimal] = Field(None, description="Minimum revenue growth")
    
    # Technical filters
    rsi_min: Optional[Decimal] = Field(None, ge=0, le=100, description="Minimum RSI")
    rsi_max: Optional[Decimal] = Field(None, ge=0, le=100, description="Maximum RSI")
    price_above_sma_20: Optional[bool] = Field(None, description="Price above 20-day SMA")
    price_above_sma_50: Optional[bool] = Field(None, description="Price above 50-day SMA")
    
    # Opportunity type filters
    opportunity_types: Optional[List[OpportunityType]] = Field(None, description="Types of opportunities to find")
    
    # Risk filters
    max_risk_level: Optional[RiskLevel] = Field(None, description="Maximum acceptable risk level")
    
    # Result filters
    limit: int = Field(50, ge=1, le=200, description="Maximum number of results")
    min_score: Optional[int] = Field(None, ge=0, le=100, description="Minimum opportunity score")
    
    @validator('market_cap_max')
    def validate_market_cap_range(cls, v, values):
        """Validate market cap range."""
        if v is not None and 'market_cap_min' in values and values['market_cap_min'] is not None:
            if v < values['market_cap_min']:
                raise ValueError('market_cap_max must be greater than market_cap_min')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "market_cap_categories": ["large_cap", "mid_cap"],
                "sectors": ["Technology", "Healthcare"],
                "pe_ratio_max": 25,
                "roe_min": 0.15,
                "opportunity_types": ["undervalued", "growth"],
                "max_risk_level": "moderate",
                "limit": 20
            }
        }


class OpportunityScore(BaseModel):
    """Detailed scoring breakdown for an opportunity."""
    
    overall_score: int = Field(..., ge=0, le=100, description="Overall opportunity score")
    fundamental_score: Optional[int] = Field(None, ge=0, le=100, description="Fundamental analysis score")
    technical_score: Optional[int] = Field(None, ge=0, le=100, description="Technical analysis score")
    momentum_score: Optional[int] = Field(None, ge=0, le=100, description="Momentum score")
    value_score: Optional[int] = Field(None, ge=0, le=100, description="Value score")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="Quality score")
    
    # Score components breakdown
    score_components: Dict[str, Decimal] = Field(default_factory=dict, description="Detailed score breakdown")


class InvestmentOpportunity(BaseModel):
    """Investment opportunity model."""
    
    # Basic stock information
    symbol: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Industry classification")
    
    # Current market data
    current_price: Decimal = Field(..., ge=0, description="Current stock price")
    market_cap: Optional[int] = Field(None, ge=0, description="Market capitalization")
    volume: int = Field(..., ge=0, description="Current volume")
    
    # Opportunity details
    opportunity_types: List[OpportunityType] = Field(..., description="Types of opportunities identified")
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    
    # Scoring
    scores: OpportunityScore = Field(..., description="Detailed scoring breakdown")
    
    # Key metrics that make this an opportunity
    key_metrics: Dict[str, Union[str, Decimal, int]] = Field(default_factory=dict, description="Key metrics")
    
    # Reasoning and analysis
    reasons: List[str] = Field(..., description="Reasons why this is an opportunity")
    risks: List[str] = Field(..., description="Key risks to consider")
    catalysts: List[str] = Field(default_factory=list, description="Potential catalysts")
    
    # Price targets and recommendations
    price_target_short: Optional[Decimal] = Field(None, description="3-month price target")
    price_target_medium: Optional[Decimal] = Field(None, description="6-month price target")
    price_target_long: Optional[Decimal] = Field(None, description="12-month price target")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now, description="Last analysis update")
    data_freshness: Dict[str, Optional[datetime]] = Field(default_factory=dict, description="Data freshness timestamps")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        return v.upper()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "current_price": 150.25,
                "market_cap": 2500000000000,
                "volume": 75000000,
                "opportunity_types": ["undervalued", "quality"],
                "risk_level": "moderate",
                "scores": {
                    "overall_score": 85,
                    "fundamental_score": 90,
                    "technical_score": 80,
                    "value_score": 85,
                    "quality_score": 95
                },
                "key_metrics": {
                    "pe_ratio": 25.5,
                    "roe": 0.31,
                    "debt_to_equity": 0.45,
                    "revenue_growth": 0.08
                },
                "reasons": [
                    "Strong balance sheet with low debt",
                    "Consistent revenue growth",
                    "High return on equity",
                    "Trading below historical P/E average"
                ],
                "risks": [
                    "High market concentration risk",
                    "Regulatory scrutiny in key markets",
                    "Supply chain dependencies"
                ],
                "price_target_short": 165.00,
                "price_target_medium": 175.00,
                "price_target_long": 190.00
            }
        }


class OpportunitySearchResult(BaseModel):
    """Search result containing opportunities and metadata."""
    
    opportunities: List[InvestmentOpportunity] = Field(..., description="List of investment opportunities")
    total_found: int = Field(..., ge=0, description="Total opportunities found (before limit)")
    filters_applied: OpportunitySearchFilters = Field(..., description="Filters that were applied")
    search_timestamp: datetime = Field(default_factory=datetime.now, description="When search was performed")
    execution_time_ms: Optional[int] = Field(None, description="Search execution time in milliseconds")
    
    # Search statistics
    stats: Dict[str, Any] = Field(default_factory=dict, description="Search statistics")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class OpportunityRanking(BaseModel):
    """Ranking criteria for opportunities."""
    
    sort_by: str = Field("overall_score", description="Primary sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    
    # Weighting for different score components
    fundamental_weight: Decimal = Field(Decimal("0.4"), ge=0, le=1, description="Weight for fundamental score")
    technical_weight: Decimal = Field(Decimal("0.3"), ge=0, le=1, description="Weight for technical score")
    momentum_weight: Decimal = Field(Decimal("0.2"), ge=0, le=1, description="Weight for momentum score")
    value_weight: Decimal = Field(Decimal("0.1"), ge=0, le=1, description="Weight for value score")
    
    @validator('technical_weight', 'momentum_weight', 'value_weight')
    def validate_weights_sum(cls, v, values):
        """Validate that all weights sum to 1.0."""
        weights = [values.get('fundamental_weight', 0), v]
        if 'technical_weight' in values:
            weights.append(values['technical_weight'])
        if 'momentum_weight' in values:
            weights.append(values['momentum_weight'])
        
        # Only validate when we have all weights
        if len(weights) == 4:
            total = sum(weights)
            if abs(total - 1.0) > 0.01:  # Allow small floating point errors
                raise ValueError('All weights must sum to 1.0')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "sort_by": "overall_score",
                "sort_order": "desc",
                "fundamental_weight": 0.5,
                "technical_weight": 0.3,
                "momentum_weight": 0.1,
                "value_weight": 0.1
            }
        }