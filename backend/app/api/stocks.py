"""
Stock lookup and market data API endpoints.
Provides endpoints for stock symbol validation, market data retrieval, and basic stock information.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..services.data_aggregation import DataAggregationService, DataAggregationException
from ..models.stock import MarketData, Stock
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])

# Response models
class StockLookupResponse(BaseModel):
    """Response model for stock lookup."""
    stock: Stock
    market_data: MarketData
    
    class Config:
        schema_extra = {
            "example": {
                "stock": {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "exchange": "NASDAQ",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "market_cap": 3000000000000,
                    "last_updated": "2024-01-15T10:30:00Z"
                },
                "market_data": {
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
        }

class SymbolValidationResponse(BaseModel):
    """Response model for symbol validation."""
    symbol: str
    is_valid: bool
    suggestions: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "is_valid": True,
                "suggestions": []
            }
        }

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
                "message": "Stock symbol INVALID not found",
                "error_type": "INVALID_SYMBOL",
                "suggestions": [
                    "Check symbol spelling",
                    "Verify symbol exists on major exchanges",
                    "Try alternative symbol formats"
                ],
                "timestamp": "2024-01-15T15:30:00Z"
            }
        }

# Dependency to get data service
def get_data_service() -> DataAggregationService:
    """Get data aggregation service instance."""
    return DataAggregationService()

@router.get("/lookup/{symbol}", response_model=StockLookupResponse)
async def lookup_stock(
    symbol: str,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    data_service: DataAggregationService = Depends(get_data_service)
):
    """
    Look up comprehensive stock information including market data.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, GOOGL)
        use_cache: Whether to use cached data if available
        
    Returns:
        Combined stock information and market data
        
    Raises:
        HTTPException: If symbol is invalid or data cannot be retrieved
    """
    try:
        logger.info(f"Looking up stock information for symbol: {symbol}")
        
        # Get both stock info and market data concurrently
        import asyncio
        stock_info_task = asyncio.create_task(
            data_service.get_stock_info(symbol, use_cache=use_cache)
        )
        market_data_task = asyncio.create_task(
            data_service.get_market_data(symbol, use_cache=use_cache)
        )
        
        stock_info, market_data = await asyncio.gather(
            stock_info_task, market_data_task
        )
        
        logger.info(f"Successfully retrieved data for {symbol}")
        return StockLookupResponse(
            stock=stock_info,
            market_data=market_data
        )
        
    except DataAggregationException as e:
        logger.warning(f"Data aggregation error for {symbol}: {e.message}")
        
        # Map error types to HTTP status codes
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
        logger.error(f"Unexpected error looking up {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while looking up stock",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later", "Contact support if problem persists"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )

@router.get("/market-data/{symbol}", response_model=MarketData)
async def get_market_data(
    symbol: str,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    data_service: DataAggregationService = Depends(get_data_service)
):
    """
    Get real-time market data for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        use_cache: Whether to use cached data if available
        
    Returns:
        Current market data including price, volume, and changes
    """
    try:
        logger.info(f"Fetching market data for symbol: {symbol}")
        market_data = await data_service.get_market_data(symbol, use_cache=use_cache)
        
        logger.info(f"Successfully retrieved market data for {symbol}")
        return market_data
        
    except DataAggregationException as e:
        logger.warning(f"Data aggregation error for {symbol}: {e.message}")
        
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
        logger.error(f"Unexpected error fetching market data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while fetching market data",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )

@router.get("/validate/{symbol}", response_model=SymbolValidationResponse)
async def validate_symbol(
    symbol: str,
    data_service: DataAggregationService = Depends(get_data_service)
):
    """
    Validate if a stock symbol exists and is tradeable.
    
    Args:
        symbol: Stock ticker symbol to validate
        
    Returns:
        Validation result with suggestions if invalid
    """
    try:
        logger.info(f"Validating symbol: {symbol}")
        
        is_valid = await data_service.validate_symbol(symbol)
        
        response = SymbolValidationResponse(
            symbol=symbol.upper(),
            is_valid=is_valid,
            suggestions=[]
        )
        
        if not is_valid:
            response.suggestions = [
                "Check symbol spelling",
                "Verify symbol exists on major exchanges",
                "Try searching by company name",
                "Check for recent ticker changes"
            ]
        
        logger.info(f"Symbol {symbol} validation result: {is_valid}")
        return response
        
    except DataAggregationException as e:
        # For validation, we return the result rather than raising an error
        logger.info(f"Symbol {symbol} validation failed: {e.message}")
        return SymbolValidationResponse(
            symbol=symbol.upper(),
            is_valid=False,
            suggestions=e.suggestions
        )
    except Exception as e:
        logger.error(f"Unexpected error validating {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error during symbol validation",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )

@router.get("/info/{symbol}", response_model=Stock)
async def get_stock_info(
    symbol: str,
    use_cache: bool = Query(True, description="Whether to use cached data"),
    data_service: DataAggregationService = Depends(get_data_service)
):
    """
    Get basic stock information (company name, sector, etc.).
    
    Args:
        symbol: Stock ticker symbol
        use_cache: Whether to use cached data if available
        
    Returns:
        Basic stock information
    """
    try:
        logger.info(f"Fetching stock info for symbol: {symbol}")
        stock_info = await data_service.get_stock_info(symbol, use_cache=use_cache)
        
        logger.info(f"Successfully retrieved stock info for {symbol}")
        return stock_info
        
    except DataAggregationException as e:
        logger.warning(f"Data aggregation error for {symbol}: {e.message}")
        
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
        logger.error(f"Unexpected error fetching stock info for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error while fetching stock info",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )

@router.post("/batch/market-data", response_model=Dict[str, MarketData])
async def get_batch_market_data(
    symbols: List[str],
    use_cache: bool = Query(True, description="Whether to use cached data"),
    data_service: DataAggregationService = Depends(get_data_service)
):
    """
    Get market data for multiple symbols at once.
    
    Args:
        symbols: List of stock ticker symbols
        use_cache: Whether to use cached data if available
        
    Returns:
        Dictionary mapping symbols to their market data
    """
    try:
        logger.info(f"Fetching batch market data for {len(symbols)} symbols")
        
        # Limit batch size to prevent abuse
        if len(symbols) > 50:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message="Too many symbols requested. Maximum 50 symbols per batch.",
                    error_type="BATCH_SIZE_EXCEEDED",
                    suggestions=["Reduce number of symbols", "Make multiple smaller requests"],
                    timestamp=datetime.utcnow().isoformat()
                ).dict()
            )
        
        results = await data_service.get_multiple_market_data(symbols)
        
        logger.info(f"Successfully retrieved batch data for {len(results)} symbols")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch market data request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error during batch request",
                error_type="INTERNAL_ERROR",
                suggestions=["Try again later", "Reduce batch size"],
                timestamp=datetime.utcnow().isoformat()
            ).dict()
        )