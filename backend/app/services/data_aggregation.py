"""
Data Aggregation Service for fetching and caching stock market data.
Integrates with yfinance for real-time stock data with error handling and caching.
"""

import yfinance as yf
import redis
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..models.stock import MarketData, Stock
from ..core.config import get_settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAggregationException(Exception):
    """Custom exception for data aggregation errors."""
    
    def __init__(self, message: str, error_type: str = "GENERAL", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class DataAggregationService:
    """
    Service for aggregating stock market data from multiple sources.
    Primary source: yfinance (Yahoo Finance)
    Includes caching, error handling, and fallback mechanisms.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize the data aggregation service."""
        self.settings = get_settings()
        
        # Initialize Redis client for caching
        if redis_client:
            self.redis_client = redis_client
        else:
            try:
                self.redis_client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
                self.redis_client = None
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Cache settings
        self.cache_ttl = {
            'market_data': 300,  # 5 minutes for market data
            'stock_info': 3600,  # 1 hour for basic stock info
            'invalid_symbols': 1800  # 30 minutes for invalid symbols
        }
    
    async def get_market_data(self, symbol: str, use_cache: bool = True) -> MarketData:
        """
        Fetch real-time market data for a stock symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
            use_cache: Whether to use cached data if available
            
        Returns:
            MarketData object with current stock information
            
        Raises:
            DataAggregationException: If data cannot be fetched or symbol is invalid
        """
        symbol = symbol.upper().strip()
        
        # Validate symbol format
        if not self._is_valid_symbol_format(symbol):
            raise DataAggregationException(
                f"Invalid symbol format: {symbol}",
                error_type="INVALID_SYMBOL",
                suggestions=["Check symbol spelling", "Use standard ticker format (e.g., AAPL)"]
            )
        
        # Check if symbol is known to be invalid
        if use_cache and self._is_cached_invalid_symbol(symbol):
            raise DataAggregationException(
                f"Symbol {symbol} is not valid or not found",
                error_type="INVALID_SYMBOL",
                suggestions=["Verify symbol exists", "Check for recent symbol changes"]
            )
        
        # Try to get from cache first
        if use_cache:
            cached_data = await self._get_cached_market_data(symbol)
            if cached_data:
                logger.info(f"Returning cached market data for {symbol}")
                return cached_data
        
        # Fetch fresh data from yfinance
        try:
            market_data = await self._fetch_market_data_from_yfinance(symbol)
            
            # Cache the successful result
            if self.redis_client:
                await self._cache_market_data(symbol, market_data)
            
            logger.info(f"Successfully fetched market data for {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            
            # Try to return stale cached data as fallback
            if use_cache:
                stale_data = await self._get_cached_market_data(symbol, allow_stale=True)
                if stale_data:
                    stale_data.is_stale = True
                    logger.warning(f"Returning stale cached data for {symbol}")
                    return stale_data
            
            # If all else fails, raise appropriate exception
            if "not found" in str(e).lower() or "invalid" in str(e).lower():
                # Cache invalid symbol to avoid repeated requests
                if self.redis_client:
                    await self._cache_invalid_symbol(symbol)
                
                raise DataAggregationException(
                    f"Stock symbol {symbol} not found",
                    error_type="INVALID_SYMBOL",
                    suggestions=[
                        "Check symbol spelling",
                        "Verify symbol exists on major exchanges",
                        "Try alternative symbol formats"
                    ]
                )
            else:
                raise DataAggregationException(
                    f"Failed to fetch data for {symbol}: {str(e)}",
                    error_type="API_ERROR",
                    suggestions=[
                        "Try again in a few moments",
                        "Check internet connection",
                        "Verify market is open"
                    ]
                )
    
    async def get_stock_info(self, symbol: str, use_cache: bool = True) -> Stock:
        """
        Fetch basic stock information (company name, sector, etc.).
        
        Args:
            symbol: Stock ticker symbol
            use_cache: Whether to use cached data if available
            
        Returns:
            Stock object with basic company information
        """
        symbol = symbol.upper().strip()
        
        # Check cache first
        if use_cache:
            cached_info = await self._get_cached_stock_info(symbol)
            if cached_info:
                return cached_info
        
        try:
            stock_info = await self._fetch_stock_info_from_yfinance(symbol)
            
            # Cache the result
            if self.redis_client:
                await self._cache_stock_info(symbol, stock_info)
            
            return stock_info
            
        except Exception as e:
            logger.error(f"Failed to fetch stock info for {symbol}: {e}")
            raise DataAggregationException(
                f"Failed to fetch stock information for {symbol}",
                error_type="API_ERROR",
                suggestions=["Try again later", "Verify symbol exists"]
            )
    
    async def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a stock symbol exists and is tradeable.
        
        Args:
            symbol: Stock ticker symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            await self.get_market_data(symbol, use_cache=True)
            return True
        except DataAggregationException as e:
            if e.error_type == "INVALID_SYMBOL":
                return False
            # For other errors (API issues), we can't determine validity
            raise e
    
    async def get_multiple_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """
        Fetch market data for multiple symbols concurrently.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to MarketData objects
        """
        results = {}
        
        # Create tasks for concurrent execution
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._safe_get_market_data(symbol))
            tasks.append((symbol, task))
        
        # Wait for all tasks to complete
        for symbol, task in tasks:
            try:
                market_data = await task
                if market_data:
                    results[symbol] = market_data
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                # Continue with other symbols
        
        return results
    
    async def _safe_get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Safely get market data without raising exceptions."""
        try:
            return await self.get_market_data(symbol)
        except Exception:
            return None
    
    async def _fetch_market_data_from_yfinance(self, symbol: str) -> MarketData:
        """Fetch market data from yfinance in a thread pool."""
        loop = asyncio.get_event_loop()
        
        def _fetch_sync():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid data
            if not info or info.get('regularMarketPrice') is None:
                raise ValueError(f"No market data available for {symbol}")
            
            return MarketData.from_yfinance(info)
        
        return await loop.run_in_executor(self.executor, _fetch_sync)
    
    async def _fetch_stock_info_from_yfinance(self, symbol: str) -> Stock:
        """Fetch basic stock information from yfinance."""
        loop = asyncio.get_event_loop()
        
        def _fetch_sync():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or not info.get('longName'):
                raise ValueError(f"No company information available for {symbol}")
            
            return Stock(
                symbol=symbol,
                name=info.get('longName', ''),
                exchange=info.get('exchange', ''),
                sector=info.get('sector'),
                industry=info.get('industry'),
                market_cap=info.get('marketCap'),
                last_updated=datetime.now()
            )
        
        return await loop.run_in_executor(self.executor, _fetch_sync)
    
    def _is_valid_symbol_format(self, symbol: str) -> bool:
        """Check if symbol has valid format."""
        if not symbol or len(symbol) < 1 or len(symbol) > 10:
            return False
        
        # Allow letters, numbers, and dots for international stocks
        return all(c.isalnum() or c in '.-' for c in symbol)
    
    async def _get_cached_market_data(self, symbol: str, allow_stale: bool = False) -> Optional[MarketData]:
        """Get market data from cache."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"market_data:{symbol}"
            cached_json = self.redis_client.get(cache_key)
            
            if cached_json:
                data = json.loads(cached_json)
                market_data = MarketData(**data)
                
                # Check if data is stale
                if not allow_stale:
                    cache_age = datetime.now() - market_data.timestamp
                    if cache_age > timedelta(seconds=self.cache_ttl['market_data']):
                        return None
                
                return market_data
        except Exception as e:
            logger.warning(f"Failed to get cached market data for {symbol}: {e}")
        
        return None
    
    async def _cache_market_data(self, symbol: str, market_data: MarketData) -> None:
        """Cache market data."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"market_data:{symbol}"
            data = market_data.dict()
            # Convert datetime and Decimal to JSON-serializable formats
            data['timestamp'] = data['timestamp'].isoformat()
            for key, value in data.items():
                if isinstance(value, Decimal):
                    data[key] = float(value)
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl['market_data'],
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to cache market data for {symbol}: {e}")
    
    async def _get_cached_stock_info(self, symbol: str) -> Optional[Stock]:
        """Get stock info from cache."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"stock_info:{symbol}"
            cached_json = self.redis_client.get(cache_key)
            
            if cached_json:
                data = json.loads(cached_json)
                return Stock(**data)
        except Exception as e:
            logger.warning(f"Failed to get cached stock info for {symbol}: {e}")
        
        return None
    
    async def _cache_stock_info(self, symbol: str, stock_info: Stock) -> None:
        """Cache stock information."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"stock_info:{symbol}"
            data = stock_info.dict()
            data['last_updated'] = data['last_updated'].isoformat()
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl['stock_info'],
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to cache stock info for {symbol}: {e}")
    
    def _is_cached_invalid_symbol(self, symbol: str) -> bool:
        """Check if symbol is cached as invalid."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"invalid_symbol:{symbol}"
            return self.redis_client.exists(cache_key)
        except Exception:
            return False
    
    async def _cache_invalid_symbol(self, symbol: str) -> None:
        """Cache symbol as invalid to avoid repeated requests."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"invalid_symbol:{symbol}"
            self.redis_client.setex(
                cache_key,
                self.cache_ttl['invalid_symbols'],
                "1"
            )
        except Exception as e:
            logger.warning(f"Failed to cache invalid symbol {symbol}: {e}")
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Clear cache for a specific symbol or all cached data."""
        if not self.redis_client:
            return
        
        try:
            if symbol:
                # Clear specific symbol cache
                symbol = symbol.upper()
                keys_to_delete = [
                    f"market_data:{symbol}",
                    f"stock_info:{symbol}",
                    f"invalid_symbol:{symbol}"
                ]
                for key in keys_to_delete:
                    self.redis_client.delete(key)
                logger.info(f"Cleared cache for symbol {symbol}")
            else:
                # Clear all cache
                keys = self.redis_client.keys("market_data:*")
                keys.extend(self.redis_client.keys("stock_info:*"))
                keys.extend(self.redis_client.keys("invalid_symbol:*"))
                if keys:
                    self.redis_client.delete(*keys)
                logger.info("Cleared all cached data")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            stats = {
                "market_data_entries": len(self.redis_client.keys("market_data:*")),
                "stock_info_entries": len(self.redis_client.keys("stock_info:*")),
                "invalid_symbols": len(self.redis_client.keys("invalid_symbol:*"))
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}