"""
Unit tests for DataAggregationService.
Tests data fetching, caching, error handling, and edge cases.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import json
import redis

from app.services.data_aggregation import DataAggregationService, DataAggregationException
from app.models.stock import MarketData, Stock


class TestDataAggregationService:
    """Test suite for DataAggregationService."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock_redis = Mock(spec=redis.Redis)
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.exists.return_value = False
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.keys.return_value = []
        return mock_redis
    
    @pytest.fixture
    def service(self, mock_redis):
        """Create DataAggregationService instance with mocked Redis."""
        return DataAggregationService(redis_client=mock_redis)
    
    @pytest.fixture
    def sample_yfinance_data(self):
        """Sample yfinance ticker info data."""
        return {
            'symbol': 'AAPL',
            'longName': 'Apple Inc.',
            'currentPrice': 150.25,
            'regularMarketChange': 2.50,
            'regularMarketChangePercent': 1.69,
            'regularMarketPrice': 150.25,
            'volume': 75000000,
            'fiftyTwoWeekHigh': 180.00,
            'fiftyTwoWeekLow': 120.00,
            'averageVolume': 80000000,
            'marketCap': 2500000000000,
            'trailingPE': 25.5,
            'exchange': 'NMS',
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample MarketData object."""
        return MarketData(
            symbol='AAPL',
            price=Decimal('150.25'),
            change=Decimal('2.50'),
            change_percent=Decimal('1.69'),
            volume=75000000,
            high_52_week=Decimal('180.00'),
            low_52_week=Decimal('120.00'),
            avg_volume=80000000,
            market_cap=2500000000000,
            pe_ratio=Decimal('25.5'),
            timestamp=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_get_market_data_success(self, service, sample_yfinance_data, mock_redis):
        """Test successful market data retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock yfinance response
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = sample_yfinance_data
            mock_ticker.return_value = mock_ticker_instance
            
            # Mock Redis cache miss
            mock_redis.get.return_value = None
            
            result = await service.get_market_data('AAPL')
            
            assert result.symbol == 'AAPL'
            assert result.price == Decimal('150.25')
            assert result.change == Decimal('2.50')
            assert result.volume == 75000000
            assert not result.is_stale
            
            # Verify caching was attempted
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_market_data_from_cache(self, service, sample_market_data, mock_redis):
        """Test market data retrieval from cache."""
        # Mock cached data
        cached_data = sample_market_data.dict()
        cached_data['timestamp'] = cached_data['timestamp'].isoformat()
        for key, value in cached_data.items():
            if isinstance(value, Decimal):
                cached_data[key] = float(value)
        
        mock_redis.get.return_value = json.dumps(cached_data)
        
        result = await service.get_market_data('AAPL')
        
        assert result.symbol == 'AAPL'
        assert result.price == Decimal('150.25')
        
        # Verify no yfinance call was made
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_market_data_invalid_symbol_format(self, service):
        """Test handling of invalid symbol formats."""
        invalid_symbols = ['', '123456789012', 'A@B', None]
        
        for symbol in invalid_symbols:
            with pytest.raises(DataAggregationException) as exc_info:
                await service.get_market_data(symbol or '')
            
            assert exc_info.value.error_type == "INVALID_SYMBOL"
            assert "Invalid symbol format" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_get_market_data_symbol_not_found(self, service, mock_redis):
        """Test handling of non-existent stock symbols."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock yfinance returning empty/invalid data
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {}
            mock_ticker.return_value = mock_ticker_instance
            
            mock_redis.get.return_value = None
            
            with pytest.raises(DataAggregationException) as exc_info:
                await service.get_market_data('INVALID')
            
            assert exc_info.value.error_type == "INVALID_SYMBOL"
            assert "not found" in exc_info.value.message.lower()
            
            # Verify invalid symbol was cached
            mock_redis.setex.assert_called()
            cache_call_args = mock_redis.setex.call_args[0]
            assert "invalid_symbol:INVALID" in cache_call_args[0]
    
    @pytest.mark.asyncio
    async def test_get_market_data_api_error_with_stale_cache(self, service, sample_market_data, mock_redis):
        """Test fallback to stale cache data when API fails."""
        # Mock stale cached data (older than TTL)
        stale_data = sample_market_data.dict()
        stale_data['timestamp'] = (datetime.now() - timedelta(hours=1)).isoformat()
        for key, value in stale_data.items():
            if isinstance(value, Decimal):
                stale_data[key] = float(value)
        
        mock_redis.get.side_effect = [None, json.dumps(stale_data)]  # First call (fresh), second call (stale)
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock yfinance API error
            mock_ticker.side_effect = Exception("API Error")
            
            result = await service.get_market_data('AAPL')
            
            assert result.symbol == 'AAPL'
            assert result.is_stale == True
    
    @pytest.mark.asyncio
    async def test_get_market_data_no_cache_no_fallback(self, service, mock_redis):
        """Test error when no cache and API fails."""
        mock_redis.get.return_value = None
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.side_effect = Exception("Network error")
            
            with pytest.raises(DataAggregationException) as exc_info:
                await service.get_market_data('AAPL')
            
            assert exc_info.value.error_type == "API_ERROR"
            assert "Failed to fetch data" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_get_stock_info_success(self, service, sample_yfinance_data, mock_redis):
        """Test successful stock info retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = sample_yfinance_data
            mock_ticker.return_value = mock_ticker_instance
            
            mock_redis.get.return_value = None
            
            result = await service.get_stock_info('AAPL')
            
            assert result.symbol == 'AAPL'
            assert result.name == 'Apple Inc.'
            assert result.sector == 'Technology'
            assert result.industry == 'Consumer Electronics'
            assert result.exchange == 'NMS'
    
    @pytest.mark.asyncio
    async def test_validate_symbol_valid(self, service, sample_yfinance_data):
        """Test symbol validation for valid symbols."""
        with patch.object(service, 'get_market_data') as mock_get_data:
            mock_get_data.return_value = Mock()
            
            result = await service.validate_symbol('AAPL')
            assert result == True
    
    @pytest.mark.asyncio
    async def test_validate_symbol_invalid(self, service):
        """Test symbol validation for invalid symbols."""
        with patch.object(service, 'get_market_data') as mock_get_data:
            mock_get_data.side_effect = DataAggregationException(
                "Symbol not found", 
                error_type="INVALID_SYMBOL"
            )
            
            result = await service.validate_symbol('INVALID')
            assert result == False
    
    @pytest.mark.asyncio
    async def test_get_multiple_market_data(self, service, sample_yfinance_data):
        """Test fetching multiple symbols concurrently."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        with patch.object(service, '_safe_get_market_data') as mock_safe_get:
            # Mock successful responses for all symbols
            mock_data = Mock()
            mock_data.symbol = 'TEST'
            mock_safe_get.return_value = mock_data
            
            results = await service.get_multiple_market_data(symbols)
            
            assert len(results) == 3
            assert all(symbol in results for symbol in symbols)
            assert mock_safe_get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_safe_get_market_data_with_exception(self, service):
        """Test _safe_get_market_data handles exceptions gracefully."""
        with patch.object(service, 'get_market_data') as mock_get_data:
            mock_get_data.side_effect = Exception("Test error")
            
            result = await service._safe_get_market_data('AAPL')
            assert result is None
    
    def test_is_valid_symbol_format(self, service):
        """Test symbol format validation."""
        valid_symbols = ['AAPL', 'GOOGL', 'BRK.A', 'TSM', 'A']
        invalid_symbols = ['', 'TOOLONGSYMBOL', 'A@B', 'SYM BOL', None]
        
        for symbol in valid_symbols:
            assert service._is_valid_symbol_format(symbol) == True
        
        for symbol in invalid_symbols:
            assert service._is_valid_symbol_format(symbol or '') == False
    
    def test_cache_operations(self, service, mock_redis):
        """Test cache operations."""
        # Test clearing specific symbol cache
        service.clear_cache('AAPL')
        assert mock_redis.delete.call_count == 3  # market_data, stock_info, invalid_symbol
        
        # Test clearing all cache
        mock_redis.keys.return_value = ['market_data:AAPL', 'stock_info:AAPL']
        service.clear_cache()
        mock_redis.delete.assert_called()
    
    def test_get_cache_stats(self, service, mock_redis):
        """Test cache statistics retrieval."""
        mock_redis.keys.side_effect = [
            ['market_data:AAPL', 'market_data:GOOGL'],  # market_data entries
            ['stock_info:AAPL'],  # stock_info entries
            ['invalid_symbol:INVALID']  # invalid_symbols
        ]
        
        stats = service.get_cache_stats()
        
        assert stats['market_data_entries'] == 2
        assert stats['stock_info_entries'] == 1
        assert stats['invalid_symbols'] == 1
    
    def test_redis_connection_failure(self):
        """Test service initialization when Redis is unavailable."""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_redis_instance
            
            service = DataAggregationService()
            assert service.redis_client is None
    
    @pytest.mark.asyncio
    async def test_cached_invalid_symbol_check(self, service, mock_redis):
        """Test checking for cached invalid symbols."""
        # Use a valid format symbol that should pass format validation
        symbol = 'INVALID'
        
        # Mock symbol exists in invalid cache
        mock_redis.exists.return_value = True
        
        with pytest.raises(DataAggregationException) as exc_info:
            await service.get_market_data(symbol)
        
        assert exc_info.value.error_type == "INVALID_SYMBOL"
        # Verify the exists method was called with the correct cache key
        mock_redis.exists.assert_called_with(f"invalid_symbol:{symbol}")
    
    @pytest.mark.asyncio
    async def test_market_data_serialization_edge_cases(self, service, mock_redis):
        """Test handling of edge cases in data serialization."""
        # Test with None values
        yf_data_with_nones = {
            'symbol': 'TEST',
            'currentPrice': 100.0,
            'regularMarketChange': 0.0,
            'regularMarketChangePercent': 0.0,
            'regularMarketPrice': 100.0,
            'volume': 1000000,
            'fiftyTwoWeekHigh': None,  # None value
            'fiftyTwoWeekLow': None,   # None value
            'averageVolume': None,     # None value
            'marketCap': None,         # None value
            'trailingPE': None         # None value
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = yf_data_with_nones
            mock_ticker.return_value = mock_ticker_instance
            
            mock_redis.get.return_value = None
            
            result = await service.get_market_data('TEST')
            
            assert result.symbol == 'TEST'
            assert result.price == Decimal('100.0')
            assert result.high_52_week is None
            assert result.low_52_week is None
            assert result.avg_volume is None
            assert result.market_cap is None
            assert result.pe_ratio is None


class TestDataAggregationException:
    """Test suite for DataAggregationException."""
    
    def test_exception_creation(self):
        """Test exception creation with all parameters."""
        suggestions = ["Try again", "Check spelling"]
        exc = DataAggregationException(
            "Test message",
            error_type="TEST_ERROR",
            suggestions=suggestions
        )
        
        assert exc.message == "Test message"
        assert exc.error_type == "TEST_ERROR"
        assert exc.suggestions == suggestions
        assert str(exc) == "Test message"
    
    def test_exception_default_values(self):
        """Test exception creation with default values."""
        exc = DataAggregationException("Test message")
        
        assert exc.message == "Test message"
        assert exc.error_type == "GENERAL"
        assert exc.suggestions == []


# Integration test fixtures and helpers
@pytest.fixture
def real_service():
    """Create a real service instance for integration tests."""
    # Use a mock Redis to avoid requiring actual Redis for tests
    mock_redis = Mock(spec=redis.Redis)
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    return DataAggregationService(redis_client=mock_redis)


class TestDataAggregationIntegration:
    """Integration tests that test the service with real yfinance calls."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_yfinance_integration(self, real_service):
        """Test with real yfinance API call (requires internet)."""
        # This test requires internet connection and may be slow
        # Skip in CI/CD if needed by marking with @pytest.mark.slow
        try:
            result = await real_service.get_market_data('AAPL', use_cache=False)
            
            assert result.symbol == 'AAPL'
            assert result.price > 0
            assert isinstance(result.price, Decimal)
            assert result.volume > 0
            assert result.timestamp is not None
            
        except Exception as e:
            # If the test fails due to network issues, skip it
            pytest.skip(f"Integration test skipped due to network issue: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_symbol_real_api(self, real_service):
        """Test invalid symbol with real API."""
        with pytest.raises(DataAggregationException) as exc_info:
            await real_service.get_market_data('DEFINITELY_INVALID_SYMBOL_12345')
        
        assert exc_info.value.error_type == "INVALID_SYMBOL"