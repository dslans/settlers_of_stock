"""
Pydantic schemas for opportunity search API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..models.opportunity import (
    OpportunitySearchFilters, OpportunityRanking, OpportunityType, 
    RiskLevel, MarketCapCategory
)


class OpportunitySearchRequest(BaseModel):
    """Request schema for opportunity search."""
    filters: OpportunitySearchFilters
    ranking: Optional[OpportunityRanking] = None
    universe: str = Field("popular", description="Stock universe to search")
    
    class Config:
        schema_extra = {
            "example": {
                "filters": {
                    "market_cap_categories": ["large_cap", "mid_cap"],
                    "sectors": ["Technology", "Healthcare"],
                    "pe_ratio_max": 25,
                    "roe_min": 0.15,
                    "opportunity_types": ["undervalued", "growth"],
                    "max_risk_level": "moderate",
                    "limit": 20
                },
                "ranking": {
                    "sort_by": "overall_score",
                    "sort_order": "desc",
                    "fundamental_weight": 0.5,
                    "technical_weight": 0.3,
                    "momentum_weight": 0.1,
                    "value_weight": 0.1
                },
                "universe": "popular"
            }
        }


class QuickSearchRequest(BaseModel):
    """Request schema for quick opportunity search."""
    opportunity_types: Optional[List[OpportunityType]] = None
    max_risk: Optional[RiskLevel] = None
    market_cap: Optional[List[MarketCapCategory]] = None
    sectors: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=50)
    
    class Config:
        schema_extra = {
            "example": {
                "opportunity_types": ["undervalued", "growth"],
                "max_risk": "moderate",
                "market_cap": ["large_cap"],
                "sectors": ["Technology"],
                "limit": 10
            }
        }


class OpportunityFilterValidation(BaseModel):
    """Response schema for filter validation."""
    valid: bool
    issues: List[str] = []
    warnings: List[str] = []
    filter_count: int
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "issues": [],
                "warnings": ["Very high ROE minimum may be too restrictive"],
                "filter_count": 5
            }
        }


class OpportunityFilterOptions(BaseModel):
    """Response schema for available filter options."""
    opportunity_types: List[str]
    risk_levels: List[str]
    market_cap_categories: List[str]
    popular_sectors: List[str]
    timeframes: List[str]
    sort_options: List[str]
    sort_orders: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "opportunity_types": ["undervalued", "growth", "momentum", "dividend"],
                "risk_levels": ["low", "moderate", "high", "very_high"],
                "market_cap_categories": ["mega_cap", "large_cap", "mid_cap", "small_cap"],
                "popular_sectors": ["Technology", "Healthcare", "Financial Services"],
                "timeframes": ["1d", "1w", "1m", "3m", "6m", "1y"],
                "sort_options": ["overall_score", "market_cap", "current_price"],
                "sort_orders": ["asc", "desc"]
            }
        }


class SimplifiedOpportunity(BaseModel):
    """Simplified opportunity for quick search responses."""
    symbol: str
    name: str
    current_price: float
    score: int
    opportunity_types: List[str]
    risk_level: str
    sector: Optional[str] = None
    market_cap: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "current_price": 150.25,
                "score": 85,
                "opportunity_types": ["undervalued", "quality"],
                "risk_level": "moderate",
                "sector": "Technology",
                "market_cap": 2500000000000
            }
        }


class QuickSearchResponse(BaseModel):
    """Response schema for quick search."""
    opportunities: List[SimplifiedOpportunity]
    total_found: int
    search_time_ms: int
    
    class Config:
        schema_extra = {
            "example": {
                "opportunities": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "current_price": 150.25,
                        "score": 85,
                        "opportunity_types": ["undervalued", "quality"],
                        "risk_level": "moderate",
                        "sector": "Technology",
                        "market_cap": 2500000000000
                    }
                ],
                "total_found": 15,
                "search_time_ms": 1250
            }
        }


class SectorOpportunityRequest(BaseModel):
    """Request schema for sector-specific opportunity search."""
    sector: str
    limit: int = Field(10, ge=1, le=50)
    min_market_cap: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "sector": "Technology",
                "limit": 10,
                "min_market_cap": 1000000000
            }
        }


class TrendingOpportunityRequest(BaseModel):
    """Request schema for trending opportunity search."""
    timeframe: str = Field("1d", regex="^(1d|1w|1m)$")
    limit: int = Field(20, ge=1, le=50)
    
    class Config:
        schema_extra = {
            "example": {
                "timeframe": "1d",
                "limit": 20
            }
        }