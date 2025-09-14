"""
Sector Analysis API endpoints.

Provides endpoints for sector performance analysis, industry comparisons,
and sector rotation identification.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..services.sector_analyzer import SectorAnalyzer, SectorAnalysisException
from ..models.sector import (
    SectorCategory, SectorAnalysisResult, IndustryAnalysisResult,
    SectorComparisonResult, SectorComparisonRequest, SectorPerformance,
    IndustryPerformance, SectorRotationSignal
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sectors", tags=["sectors"])


# Response models
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
                "message": "Failed to analyze sectors",
                "error_type": "ANALYSIS_FAILED",
                "suggestions": ["Try again later", "Check data connectivity"],
                "timestamp": "2024-01-15T15:30:00Z"
            }
        }


class SectorListResponse(BaseModel):
    """Response model for available sectors."""
    sectors: List[Dict[str, str]]
    total_count: int
    
    class Config:
        schema_extra = {
            "example": {
                "sectors": [
                    {"name": "Technology", "code": "TECHNOLOGY"},
                    {"name": "Healthcare", "code": "HEALTHCARE"},
                    {"name": "Financial Services", "code": "FINANCIAL_SERVICES"}
                ],
                "total_count": 11
            }
        }


# Dependency to get sector analyzer
def get_sector_analyzer() -> SectorAnalyzer:
    """Get sector analyzer instance."""
    return SectorAnalyzer()


@router.get("/", response_model=SectorListResponse)
async def list_sectors():
    """
    Get list of available sectors for analysis.
    
    Returns:
        List of all available sectors with their names and codes
    """
    try:
        sectors = []
        for sector in SectorCategory:
            sectors.append({
                "name": sector.value,
                "code": sector.name
            })
        
        return SectorListResponse(
            sectors=sectors,
            total_count=len(sectors)
        )
        
    except Exception as e:
        logger.error(f"Failed to list sectors: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Failed to retrieve sector list",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/analysis", response_model=SectorAnalysisResult)
async def analyze_all_sectors(
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Perform comprehensive analysis of all sectors.
    
    Returns:
        Complete sector analysis with performance rankings and rotation signals
    """
    try:
        logger.info("Starting comprehensive sector analysis")
        
        result = await analyzer.analyze_all_sectors()
        
        logger.info(f"Sector analysis completed with {len(result.sector_performances)} sectors")
        return result
        
    except SectorAnalysisException as e:
        logger.warning(f"Sector analysis error: {e.message}")
        
        status_code = 503 if e.error_type == "NO_DATA" else 500
        
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
        logger.error(f"Unexpected error in sector analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error during sector analysis",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later", "Contact support if problem persists"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/performance/{sector}", response_model=SectorPerformance)
async def get_sector_performance(
    sector: SectorCategory,
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Get detailed performance analysis for a specific sector.
    
    Args:
        sector: Sector to analyze
        
    Returns:
        Detailed sector performance metrics
    """
    try:
        logger.info(f"Getting performance analysis for {sector}")
        
        # Get full sector analysis and extract the specific sector
        full_analysis = await analyzer.analyze_all_sectors()
        
        sector_performance = next(
            (sp for sp in full_analysis.sector_performances if sp.sector == sector),
            None
        )
        
        if not sector_performance:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    message=f"Performance data not available for {sector}",
                    error_type="SECTOR_NOT_FOUND",
                    suggestions=["Check sector name", "Try again later"],
                    timestamp=datetime.utcnow().isoformat()
                ).dict()
            )
        
        logger.info(f"Retrieved performance data for {sector}")
        return sector_performance
        
    except HTTPException:
        raise
    except SectorAnalysisException as e:
        logger.warning(f"Sector performance analysis error: {e.message}")
        
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting sector performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting sector performance",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/industries/{sector}", response_model=IndustryAnalysisResult)
async def analyze_sector_industries(
    sector: SectorCategory,
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Analyze industries within a specific sector.
    
    Args:
        sector: Sector to analyze industries for
        
    Returns:
        Industry analysis result with performance and rankings
    """
    try:
        logger.info(f"Analyzing industries in {sector} sector")
        
        result = await analyzer.analyze_sector_industries(sector)
        
        logger.info(f"Analyzed {len(result.industries)} industries in {sector}")
        return result
        
    except SectorAnalysisException as e:
        logger.warning(f"Industry analysis error for {sector}: {e.message}")
        
        status_code = 404 if e.error_type == "NO_DATA" else 503
        
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
        logger.error(f"Unexpected error analyzing industries for {sector}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message=f"Internal server error analyzing industries for {sector}",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.post("/compare", response_model=SectorComparisonResult)
async def compare_sectors(
    request: SectorComparisonRequest,
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Compare performance of multiple sectors.
    
    Args:
        request: Sector comparison request with sectors and timeframe
        
    Returns:
        Sector comparison result with rankings and insights
    """
    try:
        logger.info(f"Comparing {len(request.sectors)} sectors over {request.timeframe}")
        
        result = await analyzer.compare_sectors(
            sectors=request.sectors,
            timeframe=request.timeframe
        )
        
        logger.info(f"Sector comparison completed for {len(request.sectors)} sectors")
        return result
        
    except SectorAnalysisException as e:
        logger.warning(f"Sector comparison error: {e.message}")
        
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in sector comparison: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error during sector comparison",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/rotation-signals", response_model=List[SectorRotationSignal])
async def get_rotation_signals(
    min_strength: int = Query(50, ge=0, le=100, description="Minimum signal strength"),
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Get current sector rotation signals.
    
    Args:
        min_strength: Minimum signal strength to include
        
    Returns:
        List of active sector rotation signals
    """
    try:
        logger.info(f"Getting rotation signals with minimum strength {min_strength}")
        
        # Get full analysis to extract rotation signals
        full_analysis = await analyzer.analyze_all_sectors()
        
        # Filter signals by minimum strength
        filtered_signals = [
            signal for signal in full_analysis.rotation_signals
            if signal.signal_strength >= min_strength
        ]
        
        logger.info(f"Found {len(filtered_signals)} rotation signals above strength {min_strength}")
        return filtered_signals
        
    except SectorAnalysisException as e:
        logger.warning(f"Rotation signals analysis error: {e.message}")
        
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting rotation signals: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting rotation signals",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/top-performers", response_model=Dict[str, List[str]])
async def get_top_performers(
    timeframe: str = Query("3m", description="Timeframe for performance ranking"),
    limit: int = Query(5, ge=1, le=10, description="Number of top performers to return"),
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Get top performing sectors for different timeframes.
    
    Args:
        timeframe: Timeframe for ranking (1m, 3m, 1y)
        limit: Number of top performers to return
        
    Returns:
        Dictionary with top performers for the specified timeframe
    """
    try:
        logger.info(f"Getting top {limit} sector performers for {timeframe}")
        
        # Get full analysis
        full_analysis = await analyzer.analyze_all_sectors()
        
        # Sort sectors by performance for the specified timeframe
        performance_attr = f"performance_{timeframe}"
        
        try:
            sorted_sectors = sorted(
                full_analysis.sector_performances,
                key=lambda x: getattr(x, performance_attr, 0),
                reverse=True
            )
        except AttributeError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message=f"Invalid timeframe: {timeframe}",
                    error_type="INVALID_TIMEFRAME",
                    suggestions=["Use 1d, 1w, 1m, 3m, 6m, 1y, or ytd"],
                    timestamp=datetime.utcnow().isoformat()
                ).dict()
            )
        
        top_performers = [sector.sector.value for sector in sorted_sectors[:limit]]
        
        result = {
            f"top_performers_{timeframe}": top_performers,
            "timeframe": timeframe,
            "limit": limit
        }
        
        logger.info(f"Retrieved top {limit} performers for {timeframe}")
        return result
        
    except HTTPException:
        raise
    except SectorAnalysisException as e:
        logger.warning(f"Top performers analysis error: {e.message}")
        
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting top performers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting top performers",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )


@router.get("/rankings", response_model=Dict[str, List[Dict[str, Any]]])
async def get_sector_rankings(
    sort_by: str = Query("performance_3m", description="Metric to sort by"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    analyzer: SectorAnalyzer = Depends(get_sector_analyzer)
):
    """
    Get comprehensive sector rankings by various metrics.
    
    Args:
        sort_by: Metric to sort by (performance_1m, performance_3m, etc.)
        order: Sort order (asc for ascending, desc for descending)
        
    Returns:
        Sector rankings with detailed metrics
    """
    try:
        logger.info(f"Getting sector rankings sorted by {sort_by} ({order})")
        
        # Get full analysis
        full_analysis = await analyzer.analyze_all_sectors()
        
        # Validate sort_by parameter
        valid_metrics = [
            'performance_1d', 'performance_1w', 'performance_1m', 'performance_3m',
            'performance_6m', 'performance_1y', 'performance_ytd', 'momentum_score',
            'trend_strength', 'market_cap', 'pe_ratio', 'volatility'
        ]
        
        if sort_by not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message=f"Invalid sort metric: {sort_by}",
                    error_type="INVALID_SORT_METRIC",
                    suggestions=[f"Use one of: {', '.join(valid_metrics)}"],
                    timestamp=datetime.utcnow().isoformat()
                ).dict()
            )
        
        # Sort sectors
        reverse_order = order.lower() == "desc"
        
        try:
            sorted_sectors = sorted(
                full_analysis.sector_performances,
                key=lambda x: getattr(x, sort_by, 0) or 0,
                reverse=reverse_order
            )
        except AttributeError:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message=f"Invalid sort attribute: {sort_by}",
                    error_type="INVALID_SORT_ATTRIBUTE",
                    suggestions=[f"Use one of: {', '.join(valid_metrics)}"],
                    timestamp=datetime.utcnow().isoformat()
                ).dict()
            )
        
        # Create ranking data
        rankings = []
        for rank, sector_perf in enumerate(sorted_sectors, 1):
            rankings.append({
                "rank": rank,
                "sector": sector_perf.sector.value,
                "sector_code": sector_perf.sector.name,
                sort_by: float(getattr(sector_perf, sort_by, 0) or 0),
                "performance_1m": float(sector_perf.performance_1m),
                "performance_3m": float(sector_perf.performance_3m),
                "momentum_score": sector_perf.momentum_score,
                "trend_direction": sector_perf.trend_direction.value,
                "market_cap": sector_perf.market_cap
            })
        
        result = {
            "rankings": rankings,
            "sort_by": sort_by,
            "order": order,
            "total_sectors": len(rankings)
        }
        
        logger.info(f"Generated sector rankings for {len(rankings)} sectors")
        return result
        
    except HTTPException:
        raise
    except SectorAnalysisException as e:
        logger.warning(f"Sector rankings error: {e.message}")
        
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                message=e.message,
                error_type=e.error_type,
                suggestions=e.suggestions,
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error getting sector rankings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while getting sector rankings",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )