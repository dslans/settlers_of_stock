"""
Investment Opportunity Search API endpoints.
Provides endpoints for searching, filtering, and ranking investment opportunities.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..services.opportunity_search import OpportunitySearchService, OpportunitySearchException
from ..models.opportunity import (
    OpportunitySearchFilters, InvestmentOpportunity, OpportunitySearchResult,
    OpportunityRanking, OpportunityType, RiskLevel, MarketCapCategory
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


class ErrorResponse(BaseModel):
    """Error response model."""
    error: bool = True
    message: str
    error_type: str
    suggestions: List[str] = []
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "error": True,
                "message": "Search failed due to invalid filters",
                "error_type": "INVALID_FILTERS",
                "suggestions": [
                    "Check filter values are reasonable",
                    "Reduce number of filters",
                    "Try with default filters"
                ],
                "timestamp": "2024-01-15T15:30:00Z"
            }
        }


class OpportunitySearchRequest(BaseModel):
    """Request model for opportunity search."""
    filters: OpportunitySearchFilters
    ranking: Optional[OpportunityRanking] = None
    universe: str = "popular"
    
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


class QuickSearchResponse(BaseModel):
    """Quick search response with simplified data."""
    opportunities: List[Dict[str, Any]]
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
                        "risk_level": "moderate"
                    }
                ],
                "total_found": 15,
                "search_time_ms": 1250
            }
        }


# Dependency to get opportunity search service
def get_opportunity_service() -> OpportunitySearchService:
    """Get opportunity search service instance."""
    return OpportunitySearchService()


@router.post("/search", response_model=OpportunitySearchResult)
async def search_opportunities(
    request: OpportunitySearchRequest,
    service: OpportunitySearchService = Depends(get_opportunity_service)
):
    """
    Search for investment opportunities based on specified filters and ranking criteria.
    
    Args:
        request: Search request with filters, ranking, and universe
        
    Returns:
        Comprehensive search results with detailed opportunity analysis
        
    Raises:
        HTTPException: If search fails or filters are invalid
    """
    try:
        logger.info(f"Starting opportunity search with {len(request.filters.dict(exclude_none=True))} filters")
        
        result = await service.search_opportunities(
            filters=request.filters,
            ranking=request.ranking,
            universe=request.universe
        )
        
        logger.info(f"Search completed: found {result.total_found} opportunities in {result.execution_time_ms}ms")
        return result
        
    except OpportunitySearchException as e:
        logger.warning(f"Opportunity search error: {e.message}")
        
        # Map error types to HTTP status codes
        status_code = 400 if e.error_type in ["INVALID_FILTERS", "SEARCH_ERROR"] else 503
        
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in opportunity search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error during opportunity search",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later", "Simplify search criteria"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/quick-search", response_model=QuickSearchResponse)
async def quick_search(
    opportunity_types: Optional[List[OpportunityType]] = Query(None, description="Types of opportunities"),
    max_risk: Optional[RiskLevel] = Query(None, description="Maximum risk level"),
    market_cap: Optional[List[MarketCapCategory]] = Query(None, description="Market cap categories"),
    sectors: Optional[List[str]] = Query(None, description="Sectors to include"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    service: OpportunitySearchService = Depends(get_opportunity_service)
):
    """
    Quick opportunity search with simplified parameters.
    
    Args:
        opportunity_types: Types of opportunities to find
        max_risk: Maximum acceptable risk level
        market_cap: Market cap categories to include
        sectors: Sectors to search
        limit: Maximum number of results
        
    Returns:
        Simplified search results for quick browsing
    """
    try:
        logger.info(f"Quick search with limit {limit}")
        
        # Create filters from query parameters
        filters = OpportunitySearchFilters(
            opportunity_types=opportunity_types,
            max_risk_level=max_risk,
            market_cap_categories=market_cap,
            sectors=sectors,
            limit=limit
        )
        
        result = await service.search_opportunities(filters=filters)
        
        # Simplify response for quick search
        simplified_opportunities = []
        for opp in result.opportunities:
            simplified_opportunities.append({
                "symbol": opp.symbol,
                "name": opp.name,
                "current_price": float(opp.current_price),
                "score": opp.scores.overall_score,
                "opportunity_types": [ot.value for ot in opp.opportunity_types],
                "risk_level": opp.risk_level.value,
                "sector": opp.sector,
                "market_cap": opp.market_cap
            })
        
        response = QuickSearchResponse(
            opportunities=simplified_opportunities,
            total_found=result.total_found,
            search_time_ms=result.execution_time_ms or 0
        )
        
        logger.info(f"Quick search completed: {len(simplified_opportunities)} results")
        return response
        
    except OpportunitySearchException as e:
        logger.warning(f"Quick search error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in quick search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error during quick search",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/details/{symbol}", response_model=InvestmentOpportunity)
async def get_opportunity_details(
    symbol: str,
    service: OpportunitySearchService = Depends(get_opportunity_service)
):
    """
    Get detailed opportunity analysis for a specific stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Detailed investment opportunity analysis
    """
    try:
        logger.info(f"Getting opportunity details for {symbol}")
        
        opportunity = await service.get_opportunity_details(symbol)
        
        logger.info(f"Retrieved opportunity details for {symbol}")
        return opportunity
        
    except OpportunitySearchException as e:
        logger.warning(f"Failed to get opportunity details for {symbol}: {e.message}")
        
        status_code = 404 if e.error_type == "INVALID_SYMBOL" else 503
        
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting details for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting opportunity details",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/sector/{sector}", response_model=List[InvestmentOpportunity])
async def get_sector_opportunities(
    sector: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    min_market_cap: Optional[int] = Query(None, description="Minimum market cap"),
    service: OpportunitySearchService = Depends(get_opportunity_service)
):
    """
    Find top investment opportunities within a specific sector.
    
    Args:
        sector: Sector name (e.g., 'Technology', 'Healthcare')
        limit: Maximum number of opportunities to return
        min_market_cap: Minimum market cap filter
        
    Returns:
        List of top opportunities in the specified sector
    """
    try:
        logger.info(f"Getting sector opportunities for {sector}")
        
        opportunities = await service.get_sector_opportunities(
            sector=sector,
            limit=limit,
            min_market_cap=min_market_cap
        )
        
        logger.info(f"Found {len(opportunities)} opportunities in {sector} sector")
        return opportunities
        
    except OpportunitySearchException as e:
        logger.warning(f"Failed to get sector opportunities for {sector}: {e.message}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting sector opportunities for {sector}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting sector opportunities",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/trending", response_model=List[InvestmentOpportunity])
async def get_trending_opportunities(
    timeframe: str = Query("1d", regex="^(1d|1w|1m)$", description="Timeframe for momentum"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    service: OpportunitySearchService = Depends(get_opportunity_service)
):
    """
    Find trending investment opportunities based on recent price momentum.
    
    Args:
        timeframe: Timeframe for momentum analysis ('1d', '1w', '1m')
        limit: Maximum number of opportunities to return
        
    Returns:
        List of trending opportunities with positive momentum
    """
    try:
        logger.info(f"Getting trending opportunities for {timeframe} timeframe")
        
        opportunities = await service.get_trending_opportunities(
            timeframe=timeframe,
            limit=limit
        )
        
        logger.info(f"Found {len(opportunities)} trending opportunities")
        return opportunities
        
    except OpportunitySearchException as e:
        logger.warning(f"Failed to get trending opportunities: {e.message}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting trending opportunities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting trending opportunities",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/filters/options")
async def get_filter_options():
    """
    Get available filter options for opportunity search.
    
    Returns:
        Dictionary of available filter options and their valid values
    """
    try:
        options = {
            "opportunity_types": [ot.value for ot in OpportunityType],
            "risk_levels": [rl.value for rl in RiskLevel],
            "market_cap_categories": [mc.value for mc in MarketCapCategory],
            "popular_sectors": [
                "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
                "Communication Services", "Industrials", "Consumer Defensive",
                "Energy", "Utilities", "Real Estate", "Basic Materials"
            ],
            "timeframes": ["1d", "1w", "1m", "3m", "6m", "1y"],
            "sort_options": ["overall_score", "market_cap", "current_price", "volume"],
            "sort_orders": ["asc", "desc"]
        }
        
        return options
        
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting filter options",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.post("/filters/validate")
async def validate_filters(
    filters: OpportunitySearchFilters
):
    """
    Validate opportunity search filters without performing the search.
    
    Args:
        filters: Filters to validate
        
    Returns:
        Validation result with any issues found
    """
    try:
        issues = []
        warnings = []
        
        # Validate market cap range
        if filters.market_cap_min and filters.market_cap_max:
            if filters.market_cap_min >= filters.market_cap_max:
                issues.append("market_cap_min must be less than market_cap_max")
        
        # Validate P/E ratio range
        if filters.pe_ratio_min and filters.pe_ratio_max:
            if filters.pe_ratio_min >= filters.pe_ratio_max:
                issues.append("pe_ratio_min must be less than pe_ratio_max")
        
        # Validate RSI range
        if filters.rsi_min and filters.rsi_max:
            if filters.rsi_min >= filters.rsi_max:
                issues.append("rsi_min must be less than rsi_max")
        
        # Check for potentially restrictive filters
        if filters.pe_ratio_max and filters.pe_ratio_max < 10:
            warnings.append("Very low P/E ratio maximum may exclude many opportunities")
        
        if filters.roe_min and filters.roe_min > 0.30:
            warnings.append("Very high ROE minimum may be too restrictive")
        
        if filters.limit > 100:
            warnings.append("Large result limit may impact performance")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "filter_count": len(filters.dict(exclude_none=True))
        }
        
    except Exception as e:
        logger.error(f"Error validating filters: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while validating filters",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )