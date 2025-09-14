"""
Integration tests for stock lookup and display functionality.
Tests the stock API endpoints and data aggregation service.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from app.services.data_aggregation import DataAggregationService, DataAggregationException
from app.models.stock import MarketData, Stock
from main import app

client = TestClient(app)

class TestStockLookupAPI:
    """Test stock lookup API endpoints."""
    
    def test_health_check(self):
        """Test that the API is running."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('app.api.stocks.DataAggregationService')
    def test_lookup_stock_success(self, mock_service_class):
        """Test successful stock lookup."""
        # Mock the service instance and its methods
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create mock data
        mock_stock = Stock(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            last_updated=datetime.now()
        )
        
        mock_market_data = MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00"),
            avg_volume=80000000,
            market_cap=2500000000000,
            pe_ratio=Decimal("25.5"),
            timestamp=datetime.now()
        )
        
        # Configure mock methods to return coroutines
        mock_service.get_stock_info = AsyncMock(return_value=mock_stock)
        mock_service.get_market_data = AsyncMock(return_value=mock_market_data)
        
        # Make request
        response = client.get("/api/v1/stocks/lookup/AAPL")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "stock" in data
        assert "market_data" in data
        assert data["stock"]["symbol"] == "AAPL"
        assert data["stock"]["name"] == "Apple Inc."
        assert data["market_data"]["symbol"] == "AAPL"
        assert data["market_data"]["price"] == 150.25
    
    @patch('app.api.stocks.DataAggregationService')
    def test_lookup_stock_invalid_symbol(self, mock_service_class):
        """Test stock lookup with invalid symbol."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Configure mock to raise exception for both methods
        mock_service.get_stock_info = AsyncMock(
            side_effect=DataAggregationException(
                "Stock symbol INVALID not found",
                error_type="INVALID_SYMBOL",
                suggestions=["Check symbol spelling", "Verify symbol exists"]
            )
        )
        mock_service.get_market_data = AsyncMock(
            side_effect=DataAggregationException(
                "Stock symbol INVALID not found",
                error_type="INVALID_SYMBOL",
                suggestions=["Check symbol spelling", "Verify symbol exists"]
            )
        )
        
        response = client.get("/api/v1/stocks/lookup/INVALID")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == True
        assert data["error_type"] == "INVALID_SYMBOL"
        assert "suggestions" in data
    
    @patch('app.api.stocks.DataAggregationService')
    def test_validate_symbol_valid(self, mock_service_class):
        """Test symbol validation with valid symbol."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_symbol = AsyncMock(return_value=True)
        
        response = client.get("/api/v1/stocks/validate/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["is_valid"] == True
        assert len(data["suggestions"]) == 0
    
    @patch('app.api.stocks.DataAggregationService')
    def test_validate_symbol_invalid(self, mock_service_class):
        """Test symbol validation with invalid symbol."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_symbol = AsyncMock(
            side_effect=DataAggregationException(
                "Symbol not found",
                error_type="INVALID_SYMBOL",
                suggestions=["Check spelling"]
            )
        )
        
        response = client.get("/api/v1/stocks/validate/INVALID")
        
        assert response.status_code == 200  # Validation endpoint returns 200 even for invalid
        data = response.json()
        assert data["symbol"] == "INVALID"
        assert data["is_valid"] == False
        assert len(data["suggestions"]) > 0
    
    @patch('app.api.stocks.DataAggregationService')
    def test_get_market_data(self, mock_service_class):
        """Test market data endpoint."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_market_data = MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            timestamp=datetime.now()
        )
        
        mock_service.get_market_data = AsyncMock(return_value=mock_market_data)
        
        response = client.get("/api/v1/stocks/market-data/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.25
        assert data["change"] == 2.50
    
    @patch('app.api.stocks.DataAggregationService')
    def test_batch_market_data(self, mock_service_class):
        """Test batch market data endpoint."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_results = {
            "AAPL": MarketData(
                symbol="AAPL",
                price=Decimal("150.25"),
                change=Decimal("2.50"),
                change_percent=Decimal("1.69"),
                volume=75000000,
                timestamp=datetime.now()
            ),
            "MSFT": MarketData(
                symbol="MSFT",
                price=Decimal("380.50"),
                change=Decimal("-1.25"),
                change_percent=Decimal("-0.33"),
                volume=25000000,
                timestamp=datetime.now()
            )
        }
        
        mock_service.get_multiple_market_data = AsyncMock(return_value=mock_results)
        
        response = client.post("/api/v1/stocks/batch/market-data", json=["AAPL", "MSFT"])
        
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data
        assert "MSFT" in data
        assert data["AAPL"]["symbol"] == "AAPL"
        assert data["MSFT"]["symbol"] == "MSFT"
    
    def test_batch_market_data_too_many_symbols(self):
        """Test batch endpoint with too many symbols."""
        symbols = [f"SYM{i}" for i in range(51)]  # 51 symbols, over the limit
        
        response = client.post("/api/v1/stocks/batch/market-data", json=symbols)
        
        assert response.status_code == 400
        data = response.json()
        # The error response structure is different - it's directly in the response
        assert "Too many symbols" in data["message"]


class TestDataAggregationService:
    """Test the data aggregation service directly."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return DataAggregationService(redis_client=None)  # No Redis for tests
    
    @pytest.mark.asyncio
    async def test_symbol_format_validation(self, service):
        """Test symbol format validation."""
        # Valid formats
        assert service._is_valid_symbol_format("AAPL")
        assert service._is_valid_symbol_format("BRK.A")
        assert service._is_valid_symbol_format("GOOGL")
        
        # Invalid formats
        assert not service._is_valid_symbol_format("")
        assert not service._is_valid_symbol_format("A" * 11)  # Too long
        assert not service._is_valid_symbol_format("AAPL@")  # Invalid character
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_fetch_market_data_success(self, mock_ticker, service):
        """Test successful market data fetching."""
        # Mock yfinance response
        mock_info = {
            'symbol': 'AAPL',
            'currentPrice': 150.25,  # Use currentPrice instead of regularMarketPrice
            'regularMarketPrice': 150.25,  # Keep both for compatibility
            'regularMarketChange': 2.50,
            'regularMarketChangePercent': 1.69,
            'volume': 75000000,
            'fiftyTwoWeekHigh': 180.00,
            'fiftyTwoWeekLow': 120.00,
            'averageVolume': 80000000,
            'marketCap': 2500000000000,
            'trailingPE': 25.5
        }
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance
        
        # Test the method
        result = await service._fetch_market_data_from_yfinance("AAPL")
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert result.price == Decimal("150.25")
        assert result.change == Decimal("2.50")
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_fetch_market_data_invalid_symbol(self, mock_ticker, service):
        """Test market data fetching with invalid symbol."""
        # Mock yfinance response for invalid symbol
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {}  # Empty info indicates invalid symbol
        mock_ticker.return_value = mock_ticker_instance
        
        # Test that it raises an exception
        with pytest.raises(ValueError, match="No market data available"):
            await service._fetch_market_data_from_yfinance("INVALID")
    
    @pytest.mark.asyncio
    async def test_validate_symbol_invalid_format(self, service):
        """Test symbol validation with invalid format."""
        with pytest.raises(DataAggregationException) as exc_info:
            await service.get_market_data("INVALID@SYMBOL")
        
        assert exc_info.value.error_type == "INVALID_SYMBOL"
        assert "Invalid symbol format" in exc_info.value.message
    
    @pytest.mark.asyncio
    @patch.object(DataAggregationService, 'get_market_data')
    async def test_validate_symbol_api_call(self, mock_get_market_data, service):
        """Test symbol validation makes correct API call."""
        # Mock successful market data fetch
        mock_market_data = MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            timestamp=datetime.now()
        )
        mock_get_market_data.return_value = mock_market_data
        
        result = await service.validate_symbol("AAPL")
        
        assert result == True
        mock_get_market_data.assert_called_once_with("AAPL", use_cache=True)
    
    @pytest.mark.asyncio
    async def test_get_multiple_market_data(self, service):
        """Test fetching multiple market data concurrently."""
        symbols = ["AAPL", "MSFT", "INVALID"]
        
        # Mock the _safe_get_market_data method
        async def mock_safe_get(symbol):
            if symbol == "INVALID":
                return None
            return MarketData(
                symbol=symbol,
                price=Decimal("100.00"),
                change=Decimal("1.00"),
                change_percent=Decimal("1.00"),
                volume=1000000,
                timestamp=datetime.now()
            )
        
        with patch.object(service, '_safe_get_market_data', side_effect=mock_safe_get):
            results = await service.get_multiple_market_data(symbols)
        
        assert len(results) == 2  # Only valid symbols
        assert "AAPL" in results
        assert "MSFT" in results
        assert "INVALID" not in results


class TestStockLookupIntegration:
    """Integration tests for the complete stock lookup workflow."""
    
    def test_complete_stock_lookup_workflow(self):
        """Test the complete workflow from API request to response."""
        # This test would require a real yfinance connection
        # For now, we'll test with a known stable symbol
        
        # Test validation first
        response = client.get("/api/v1/stocks/validate/AAPL")
        assert response.status_code == 200
        
        # Note: Actual integration with yfinance would be tested in a separate
        # integration test suite that runs against real APIs
    
    def test_error_handling_workflow(self):
        """Test error handling in the complete workflow."""
        # Test with clearly invalid symbol
        response = client.get("/api/v1/stocks/lookup/THISISNOTAVALIDSTOCKSYMBOL123")
        
        # Should return 404 or 503 depending on the error
        assert response.status_code in [404, 503]
        
        if response.status_code == 404:
            data = response.json()
            # The error response structure is different
            assert data["error"] == True
            assert "suggestions" in data


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])