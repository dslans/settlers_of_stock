"""
Sector and Industry Analysis Models.

This module defines data models for sector performance analysis, industry comparisons,
and sector rotation identification.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SectorCategory(str, Enum):
    """Major sector categories."""
    TECHNOLOGY = "Technology"
    HEALTHCARE = "Healthcare"
    FINANCIAL_SERVICES = "Financial Services"
    CONSUMER_CYCLICAL = "Consumer Cyclical"
    CONSUMER_DEFENSIVE = "Consumer Defensive"
    COMMUNICATION_SERVICES = "Communication Services"
    INDUSTRIALS = "Industrials"
    ENERGY = "Energy"
    UTILITIES = "Utilities"
    REAL_ESTATE = "Real Estate"
    MATERIALS = "Materials"


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    STRONG_UP = "strong_up"
    UP = "up"
    SIDEWAYS = "sideways"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


class RotationPhase(str, Enum):
    """Sector rotation phases."""
    EARLY_CYCLE = "early_cycle"
    MID_CYCLE = "mid_cycle"
    LATE_CYCLE = "late_cycle"
    RECESSION = "recession"


class SectorPerformance(BaseModel):
    """Sector performance metrics."""
    
    sector: SectorCategory = Field(..., description="Sector name")
    
    # Performance metrics
    performance_1d: Decimal = Field(..., description="1-day performance (%)")
    performance_1w: Decimal = Field(..., description="1-week performance (%)")
    performance_1m: Decimal = Field(..., description="1-month performance (%)")
    performance_3m: Decimal = Field(..., description="3-month performance (%)")
    performance_6m: Decimal = Field(..., description="6-month performance (%)")
    performance_1y: Decimal = Field(..., description="1-year performance (%)")
    performance_ytd: Decimal = Field(..., description="Year-to-date performance (%)")
    
    # Relative performance vs market
    relative_performance_1m: Decimal = Field(..., description="1-month relative to market (%)")
    relative_performance_3m: Decimal = Field(..., description="3-month relative to market (%)")
    relative_performance_1y: Decimal = Field(..., description="1-year relative to market (%)")
    
    # Trend analysis
    trend_direction: TrendDirection = Field(..., description="Current trend direction")
    trend_strength: int = Field(..., ge=0, le=100, description="Trend strength (0-100)")
    momentum_score: int = Field(..., ge=0, le=100, description="Momentum score (0-100)")
    
    # Market metrics
    market_cap: int = Field(..., ge=0, description="Total sector market cap")
    avg_volume: int = Field(..., ge=0, description="Average daily volume")
    pe_ratio: Optional[Decimal] = Field(None, description="Sector average P/E ratio")
    pb_ratio: Optional[Decimal] = Field(None, description="Sector average P/B ratio")
    
    # Rankings
    performance_rank_1m: int = Field(..., ge=1, description="1-month performance rank")
    performance_rank_3m: int = Field(..., ge=1, description="3-month performance rank")
    performance_rank_1y: int = Field(..., ge=1, description="1-year performance rank")
    
    # Additional metrics
    volatility: Decimal = Field(..., ge=0, description="Sector volatility (annualized)")
    beta: Optional[Decimal] = Field(None, description="Sector beta vs market")
    dividend_yield: Optional[Decimal] = Field(None, description="Average dividend yield")
    
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "sector": "Technology",
                "performance_1d": 1.2,
                "performance_1w": 3.5,
                "performance_1m": 8.7,
                "performance_3m": 15.2,
                "performance_6m": 22.1,
                "performance_1y": 28.5,
                "performance_ytd": 18.3,
                "relative_performance_1m": 2.1,
                "relative_performance_3m": 4.8,
                "relative_performance_1y": 8.2,
                "trend_direction": "up",
                "trend_strength": 75,
                "momentum_score": 82,
                "market_cap": 15000000000000,
                "avg_volume": 2500000000,
                "pe_ratio": 28.5,
                "pb_ratio": 4.2,
                "performance_rank_1m": 2,
                "performance_rank_3m": 1,
                "performance_rank_1y": 3,
                "volatility": 24.5,
                "beta": 1.15,
                "dividend_yield": 1.2,
                "last_updated": "2024-01-15T15:30:00Z"
            }
        }


class IndustryPerformance(BaseModel):
    """Industry performance within a sector."""
    
    industry: str = Field(..., description="Industry name")
    sector: SectorCategory = Field(..., description="Parent sector")
    
    # Performance metrics
    performance_1d: Decimal = Field(..., description="1-day performance (%)")
    performance_1w: Decimal = Field(..., description="1-week performance (%)")
    performance_1m: Decimal = Field(..., description="1-month performance (%)")
    performance_3m: Decimal = Field(..., description="3-month performance (%)")
    performance_1y: Decimal = Field(..., description="1-year performance (%)")
    
    # Relative performance vs sector
    relative_to_sector_1m: Decimal = Field(..., description="1-month relative to sector (%)")
    relative_to_sector_3m: Decimal = Field(..., description="3-month relative to sector (%)")
    relative_to_sector_1y: Decimal = Field(..., description="1-year relative to sector (%)")
    
    # Valuation metrics
    avg_pe_ratio: Optional[Decimal] = Field(None, description="Industry average P/E ratio")
    avg_pb_ratio: Optional[Decimal] = Field(None, description="Industry average P/B ratio")
    avg_roe: Optional[Decimal] = Field(None, description="Industry average ROE")
    avg_profit_margin: Optional[Decimal] = Field(None, description="Industry average profit margin")
    
    # Growth metrics
    revenue_growth: Optional[Decimal] = Field(None, description="Average revenue growth")
    earnings_growth: Optional[Decimal] = Field(None, description="Average earnings growth")
    
    # Market metrics
    market_cap: int = Field(..., ge=0, description="Total industry market cap")
    stock_count: int = Field(..., ge=1, description="Number of stocks in industry")
    
    # Rankings within sector
    performance_rank: int = Field(..., ge=1, description="Performance rank within sector")
    valuation_rank: int = Field(..., ge=1, description="Valuation rank within sector")
    growth_rank: int = Field(..., ge=1, description="Growth rank within sector")
    
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "industry": "Software - Application",
                "sector": "Technology",
                "performance_1d": 1.5,
                "performance_1w": 4.2,
                "performance_1m": 12.3,
                "performance_3m": 18.7,
                "performance_1y": 35.2,
                "relative_to_sector_1m": 3.6,
                "relative_to_sector_3m": 3.5,
                "relative_to_sector_1y": 6.7,
                "avg_pe_ratio": 32.5,
                "avg_pb_ratio": 5.8,
                "avg_roe": 0.18,
                "avg_profit_margin": 0.22,
                "revenue_growth": 0.15,
                "earnings_growth": 0.12,
                "market_cap": 3500000000000,
                "stock_count": 45,
                "performance_rank": 2,
                "valuation_rank": 8,
                "growth_rank": 3,
                "last_updated": "2024-01-15T15:30:00Z"
            }
        }


class SectorRotationSignal(BaseModel):
    """Sector rotation signal and analysis."""
    
    from_sector: SectorCategory = Field(..., description="Sector losing momentum")
    to_sector: SectorCategory = Field(..., description="Sector gaining momentum")
    
    # Signal strength
    signal_strength: int = Field(..., ge=0, le=100, description="Rotation signal strength (0-100)")
    confidence: int = Field(..., ge=0, le=100, description="Signal confidence (0-100)")
    
    # Rotation metrics
    momentum_shift: Decimal = Field(..., description="Momentum shift magnitude")
    relative_strength_change: Decimal = Field(..., description="Relative strength change")
    volume_confirmation: bool = Field(..., description="Volume confirms rotation")
    
    # Market context
    market_phase: RotationPhase = Field(..., description="Current market cycle phase")
    economic_driver: str = Field(..., description="Primary economic driver")
    
    # Timing
    signal_date: datetime = Field(..., description="When signal was first detected")
    expected_duration: str = Field(..., description="Expected rotation duration")
    
    # Supporting evidence
    reasons: List[str] = Field(..., description="Reasons supporting the rotation")
    risks: List[str] = Field(..., description="Risks to the rotation thesis")
    
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "from_sector": "Technology",
                "to_sector": "Energy",
                "signal_strength": 75,
                "confidence": 68,
                "momentum_shift": 8.5,
                "relative_strength_change": 12.3,
                "volume_confirmation": True,
                "market_phase": "mid_cycle",
                "economic_driver": "Rising interest rates and inflation",
                "signal_date": "2024-01-10T09:30:00Z",
                "expected_duration": "2-3 months",
                "reasons": [
                    "Technology sector showing relative weakness",
                    "Energy sector benefiting from higher oil prices",
                    "Value rotation gaining momentum"
                ],
                "risks": [
                    "Geopolitical tensions could reverse energy gains",
                    "Technology oversold conditions may lead to bounce"
                ],
                "last_updated": "2024-01-15T15:30:00Z"
            }
        }


class SectorAnalysisResult(BaseModel):
    """Complete sector analysis result."""
    
    # Sector performance data
    sector_performances: List[SectorPerformance] = Field(..., description="All sector performances")
    
    # Top performers
    top_performers_1m: List[SectorCategory] = Field(..., description="Top 1-month performers")
    top_performers_3m: List[SectorCategory] = Field(..., description="Top 3-month performers")
    top_performers_1y: List[SectorCategory] = Field(..., description="Top 1-year performers")
    
    # Bottom performers
    bottom_performers_1m: List[SectorCategory] = Field(..., description="Bottom 1-month performers")
    bottom_performers_3m: List[SectorCategory] = Field(..., description="Bottom 3-month performers")
    bottom_performers_1y: List[SectorCategory] = Field(..., description="Bottom 1-year performers")
    
    # Rotation signals
    rotation_signals: List[SectorRotationSignal] = Field(..., description="Active rotation signals")
    
    # Market context
    market_trend: TrendDirection = Field(..., description="Overall market trend")
    market_phase: RotationPhase = Field(..., description="Current market cycle phase")
    volatility_regime: str = Field(..., description="Current volatility regime")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    data_freshness: Dict[str, datetime] = Field(..., description="Data freshness by source")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class IndustryAnalysisResult(BaseModel):
    """Industry analysis result for a specific sector."""
    
    sector: SectorCategory = Field(..., description="Analyzed sector")
    industries: List[IndustryPerformance] = Field(..., description="Industry performances")
    
    # Top industries within sector
    top_performing_industries: List[str] = Field(..., description="Top performing industries")
    best_value_industries: List[str] = Field(..., description="Best value industries")
    highest_growth_industries: List[str] = Field(..., description="Highest growth industries")
    
    # Sector summary
    sector_summary: SectorPerformance = Field(..., description="Overall sector performance")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class SectorComparisonRequest(BaseModel):
    """Request for sector comparison analysis."""
    
    sectors: List[SectorCategory] = Field(..., min_items=2, max_items=6, description="Sectors to compare")
    timeframe: str = Field("3m", description="Comparison timeframe")
    metrics: List[str] = Field(
        default=["performance", "valuation", "momentum"],
        description="Metrics to compare"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "sectors": ["Technology", "Healthcare", "Financial Services"],
                "timeframe": "3m",
                "metrics": ["performance", "valuation", "momentum"]
            }
        }


class SectorComparisonResult(BaseModel):
    """Result of sector comparison analysis."""
    
    sectors: List[SectorCategory] = Field(..., description="Compared sectors")
    timeframe: str = Field(..., description="Comparison timeframe")
    
    # Performance comparison
    performance_ranking: List[Dict[str, Any]] = Field(..., description="Performance rankings")
    
    # Valuation comparison
    valuation_ranking: List[Dict[str, Any]] = Field(..., description="Valuation rankings")
    
    # Momentum comparison
    momentum_ranking: List[Dict[str, Any]] = Field(..., description="Momentum rankings")
    
    # Summary insights
    winner: SectorCategory = Field(..., description="Overall best performing sector")
    best_value: SectorCategory = Field(..., description="Best value sector")
    strongest_momentum: SectorCategory = Field(..., description="Strongest momentum sector")
    
    # Analysis insights
    key_insights: List[str] = Field(..., description="Key analysis insights")
    recommendations: List[str] = Field(..., description="Investment recommendations")
    
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }