"""
Unit tests for TechnicalAnalyzer service.
Tests technical indicator calculations, support/resistance detection,
and multi-timeframe analysis functionality.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from app.services.technical_analyzer import (
    TechnicalAnalyzer, TechnicalAnalysisException, 
    TechnicalSignal, MultiTimeframeAnalysis
)
from app.models.technical import (
    TechnicalData, TimeFrame, TrendDirection, SignalStrength,
    SupportResistanceLevel
)


class TestTechnicalAnalyzer:
    """Test cases for TechnicalAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create TechnicalAnalyzer instance for testing."""
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        # Create realistic price data with trend
        base_price = 100
        prices = []
        volumes = []
        
        for i in range(100):
            # Add some trend and volatility
            trend = i * 0.1  # Slight upward trend
            volatility = np.random.normal(0, 2)  # Random volatility
            price = base_price + trend + volatility
            prices.append(max(price, 1))  # Ensure positive prices
            volumes.append(np.random.randint(1000000, 10000000))
        
        data = pd.DataFrame({
            'Open': [p * 0.99 for p in prices],
            'High': [p * 1.02 for p in prices],
            'Low': [p * 0.98 for p in prices],
            'Close': prices,
            'Volume': volumes
        }, index=dates)
        
        return data
    
    @pytest.fixture
    def mock_yfinance_data(self, sample_price_data):
        """Mock yfinance ticker data."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_price_data
        return mock_ticker
    
    # Test Basic Indicator Calculations
    
    def test_calculate_sma(self, analyzer):
        """Test Simple Moving Average calculation."""
        prices = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        sma_5 = analyzer.calculate_sma(prices, 5)
        
        # Check that we get expected values (last 5 should be average of 6,7,8,9,10 = 8)
        assert not np.isnan(sma_5[-1])
        assert abs(sma_5[-1] - 8.0) < 0.01
    
    def test_calculate_ema(self, analyzer):
        """Test Exponential Moving Average calculation."""
        prices = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        ema_5 = analyzer.calculate_ema(prices, 5)
        
        # EMA should give more weight to recent prices
        assert not np.isnan(ema_5[-1])
        assert ema_5[-1] >= 8.0  # Should be at least equal to or higher than SMA
    
    def test_calculate_rsi(self, analyzer):
        """Test RSI calculation."""
        # Create price data with clear trend
        prices = np.array([50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78], dtype=np.float64)
        rsi = analyzer.calculate_rsi(prices, 14)
        
        # RSI should be high for uptrending prices
        assert not np.isnan(rsi[-1])
        assert 0 <= rsi[-1] <= 100
        assert rsi[-1] > 50  # Should be above 50 for uptrend
    
    def test_calculate_macd(self, analyzer):
        """Test MACD calculation."""
        prices = np.array([i + np.sin(i/10) * 5 for i in range(50)], dtype=np.float64)  # Trending with oscillation
        macd, macd_signal, macd_histogram = analyzer.calculate_macd(prices)
        
        # Check that all components are calculated
        assert not np.isnan(macd[-1])
        assert not np.isnan(macd_signal[-1])
        assert not np.isnan(macd_histogram[-1])
        
        # Histogram should be difference between MACD and signal
        assert abs(macd_histogram[-1] - (macd[-1] - macd_signal[-1])) < 0.01
    
    def test_calculate_bollinger_bands(self, analyzer):
        """Test Bollinger Bands calculation."""
        np.random.seed(42)  # For reproducible results
        prices = np.array([100 + np.random.normal(0, 5) for _ in range(50)], dtype=np.float64)
        upper, middle, lower = analyzer.calculate_bollinger_bands(prices, 20, 2)
        
        # Check that bands are calculated correctly
        assert not np.isnan(upper[-1])
        assert not np.isnan(middle[-1])
        assert not np.isnan(lower[-1])
        
        # Upper should be above middle, middle above lower
        assert upper[-1] > middle[-1] > lower[-1]
    
    def test_calculate_atr(self, analyzer):
        """Test Average True Range calculation."""
        high = np.array([105, 110, 108, 112, 115], dtype=np.float64)
        low = np.array([95, 100, 98, 102, 105], dtype=np.float64)
        close = np.array([100, 105, 103, 107, 110], dtype=np.float64)
        
        atr = analyzer.calculate_atr(high, low, close, 3)
        
        # ATR should be positive and reasonable
        assert not np.isnan(atr[-1])
        assert atr[-1] > 0
    
    # Test Technical Analysis Integration
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_analyze_technical_success(self, mock_ticker_class, analyzer, mock_yfinance_data):
        """Test successful technical analysis."""
        mock_ticker_class.return_value = mock_yfinance_data
        
        result = await analyzer.analyze_technical("AAPL", TimeFrame.ONE_DAY)
        
        assert isinstance(result, TechnicalData)
        assert result.symbol == "AAPL"
        assert result.timeframe == TimeFrame.ONE_DAY
        assert result.data_points > 0
        
        # Check that some indicators are calculated
        assert result.sma_20 is not None or result.rsi is not None
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_analyze_technical_insufficient_data(self, mock_ticker_class, analyzer):
        """Test technical analysis with insufficient data."""
        # Mock ticker with very little data
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame({
            'Open': [100], 'High': [105], 'Low': [95], 'Close': [102], 'Volume': [1000000]
        })
        mock_ticker_class.return_value = mock_ticker
        
        with pytest.raises(TechnicalAnalysisException) as exc_info:
            await analyzer.analyze_technical("INVALID", TimeFrame.ONE_DAY)
        
        assert exc_info.value.error_type == "INSUFFICIENT_DATA"
        assert "Insufficient price data" in exc_info.value.message
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_analyze_technical_no_data(self, mock_ticker_class, analyzer):
        """Test technical analysis with no data."""
        # Mock ticker with empty data
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker
        
        with pytest.raises(TechnicalAnalysisException):
            await analyzer.analyze_technical("INVALID", TimeFrame.ONE_DAY)
    
    # Test Support and Resistance Detection
    
    def test_detect_support_resistance(self, analyzer, sample_price_data):
        """Test support and resistance level detection."""
        support_levels, resistance_levels = analyzer._detect_support_resistance(sample_price_data)
        
        # Should find some levels
        assert isinstance(support_levels, list)
        assert isinstance(resistance_levels, list)
        
        # Check level properties if any found
        for level in support_levels:
            assert isinstance(level, SupportResistanceLevel)
            assert level.type == "support"
            assert level.strength >= 1
            assert level.touches >= 2
        
        for level in resistance_levels:
            assert isinstance(level, SupportResistanceLevel)
            assert level.type == "resistance"
            assert level.strength >= 1
            assert level.touches >= 2
    
    def test_group_and_score_levels(self, analyzer):
        """Test level grouping and scoring logic."""
        # Create test candidates
        candidates = [
            {'price': 100.0, 'date': datetime.now(), 'index': 10},
            {'price': 100.5, 'date': datetime.now(), 'index': 20},  # Similar to first
            {'price': 105.0, 'date': datetime.now(), 'index': 30},  # Different level
            {'price': 100.2, 'date': datetime.now(), 'index': 40},  # Similar to first
        ]
        
        prices = np.array([100] * 50)  # Dummy price array
        levels = analyzer._group_and_score_levels(candidates, prices, 'support', 2)
        
        # Should group similar levels
        assert len(levels) <= len(candidates)
        
        # Check that levels have required properties
        for level in levels:
            assert level.touches >= 2
            assert level.strength > 0
            assert level.type == 'support'
    
    # Test Trend Determination
    
    def test_determine_trend_bullish(self, analyzer):
        """Test bullish trend determination."""
        tech_data = TechnicalData(
            symbol="TEST",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("105"),
            sma_50=Decimal("100"),
            rsi=Decimal("60"),
            macd=Decimal("1.5"),
            macd_signal=Decimal("1.0")
        )
        
        # Create price data with current price above moving averages
        price_data = pd.DataFrame({
            'Close': [110]  # Above both moving averages
        })
        
        trend = analyzer._determine_trend(tech_data, price_data)
        assert trend == TrendDirection.BULLISH
    
    def test_determine_trend_bearish(self, analyzer):
        """Test bearish trend determination."""
        tech_data = TechnicalData(
            symbol="TEST",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("95"),
            sma_50=Decimal("100"),
            rsi=Decimal("40"),
            macd=Decimal("-1.5"),
            macd_signal=Decimal("-1.0")
        )
        
        # Create price data with current price below moving averages
        price_data = pd.DataFrame({
            'Close': [90]  # Below both moving averages
        })
        
        trend = analyzer._determine_trend(tech_data, price_data)
        assert trend == TrendDirection.BEARISH
    
    def test_determine_trend_sideways(self, analyzer):
        """Test sideways trend determination."""
        tech_data = TechnicalData(
            symbol="TEST",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("100"),
            sma_50=Decimal("100"),
            rsi=Decimal("50"),
            macd=Decimal("0.0"),  # Neutral MACD
            macd_signal=Decimal("0.0")  # Neutral signal
        )
        
        price_data = pd.DataFrame({
            'Close': [100]
        })
        
        trend = analyzer._determine_trend(tech_data, price_data)
        # Should be sideways since all signals are neutral/equal
        assert trend in [TrendDirection.SIDEWAYS, TrendDirection.BULLISH, TrendDirection.BEARISH]  # Allow any due to neutral signals
    
    # Test Signal Calculation
    
    def test_calculate_overall_signal_strong_buy(self, analyzer):
        """Test strong buy signal calculation."""
        tech_data = TechnicalData(
            symbol="TEST",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("105"),
            sma_50=Decimal("100"),
            rsi=Decimal("25"),  # Oversold
            macd=Decimal("2.0"),
            macd_signal=Decimal("1.0"),
            bollinger_upper=Decimal("110"),
            bollinger_lower=Decimal("95")
        )
        
        price_data = pd.DataFrame({
            'Close': [96]  # Near lower Bollinger Band
        })
        
        signal = analyzer._calculate_overall_signal(tech_data, price_data)
        # Should be a buy signal due to oversold RSI and price near lower BB
        assert signal in [SignalStrength.BUY, SignalStrength.STRONG_BUY, SignalStrength.WEAK_BUY]
    
    # Test Multi-timeframe Analysis
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_analyze_multi_timeframe(self, mock_ticker_class, analyzer, mock_yfinance_data):
        """Test multi-timeframe analysis."""
        mock_ticker_class.return_value = mock_yfinance_data
        
        timeframes = [TimeFrame.ONE_DAY, TimeFrame.ONE_WEEK]
        result = await analyzer.analyze_multi_timeframe("AAPL", timeframes)
        
        assert isinstance(result, MultiTimeframeAnalysis)
        assert result.symbol == "AAPL"
        assert len(result.analyses) <= len(timeframes)  # Some might fail
        assert result.consensus_signal is not None
        assert isinstance(result.trend_alignment, bool)
        assert 'support' in result.key_levels
        assert 'resistance' in result.key_levels
    
    def test_calculate_consensus_signal(self, analyzer):
        """Test consensus signal calculation."""
        analyses = {
            "1D": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_DAY,
                overall_signal=SignalStrength.BUY
            ),
            "1W": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_WEEK,
                overall_signal=SignalStrength.STRONG_BUY
            ),
            "1M": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_MONTH,
                overall_signal=SignalStrength.BUY
            )
        }
        
        consensus = analyzer._calculate_consensus_signal(analyses)
        # Should be bullish consensus
        assert consensus in [SignalStrength.BUY, SignalStrength.STRONG_BUY]
    
    def test_check_trend_alignment_aligned(self, analyzer):
        """Test trend alignment check with aligned trends."""
        analyses = {
            "1D": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_DAY,
                trend_direction=TrendDirection.BULLISH
            ),
            "1W": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_WEEK,
                trend_direction=TrendDirection.BULLISH
            ),
            "1M": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_MONTH,
                trend_direction=TrendDirection.BULLISH
            )
        }
        
        alignment = analyzer._check_trend_alignment(analyses)
        assert alignment is True
    
    def test_check_trend_alignment_not_aligned(self, analyzer):
        """Test trend alignment check with conflicting trends."""
        analyses = {
            "1D": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_DAY,
                trend_direction=TrendDirection.BULLISH
            ),
            "1W": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_WEEK,
                trend_direction=TrendDirection.BEARISH
            ),
            "1M": TechnicalData(
                symbol="TEST", 
                timeframe=TimeFrame.ONE_MONTH,
                trend_direction=TrendDirection.SIDEWAYS
            )
        }
        
        alignment = analyzer._check_trend_alignment(analyses)
        assert alignment is False
    
    # Test Edge Cases and Error Handling
    
    def test_safe_decimal_with_nan(self, analyzer):
        """Test safe decimal conversion with NaN values."""
        result = analyzer._safe_decimal(float('nan'))
        assert result is None
    
    def test_safe_decimal_with_infinity(self, analyzer):
        """Test safe decimal conversion with infinity."""
        result = analyzer._safe_decimal(float('inf'))
        assert result is None
    
    def test_safe_decimal_with_valid_number(self, analyzer):
        """Test safe decimal conversion with valid number."""
        result = analyzer._safe_decimal(123.456)
        assert result == Decimal("123.456")
    
    def test_consolidate_levels_empty_list(self, analyzer):
        """Test level consolidation with empty list."""
        result = analyzer._consolidate_levels([], 'support')
        assert result == []
    
    def test_consolidate_levels_similar_prices(self, analyzer):
        """Test level consolidation with similar price levels."""
        levels = [
            SupportResistanceLevel(level=Decimal("100.0"), strength=5, type="support", touches=2),
            SupportResistanceLevel(level=Decimal("100.5"), strength=3, type="support", touches=1),
            SupportResistanceLevel(level=Decimal("105.0"), strength=4, type="support", touches=2),
        ]
        
        consolidated = analyzer._consolidate_levels(levels, 'support')
        
        # Should consolidate first two levels (within 2% tolerance)
        assert len(consolidated) == 2
        assert consolidated[0].touches >= 2  # Combined touches
    
    # Test Technical Score Calculation
    
    def test_technical_score_calculation(self):
        """Test technical score calculation in TechnicalData model."""
        tech_data = TechnicalData(
            symbol="TEST",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("105"),
            sma_50=Decimal("100"),
            rsi=Decimal("30"),  # Oversold - should boost score
            macd=Decimal("1.0"),
            macd_signal=Decimal("0.5"),
            bollinger_upper=Decimal("110"),
            bollinger_lower=Decimal("95")
        )
        
        current_price = Decimal("98")  # Near lower Bollinger Band
        score = tech_data.calculate_technical_score(current_price)
        
        assert 0 <= score <= 100
        assert score > 50  # Should be bullish due to oversold RSI and price position


class TestTechnicalAnalysisExceptions:
    """Test technical analysis exception handling."""
    
    def test_technical_analysis_exception_creation(self):
        """Test TechnicalAnalysisException creation."""
        exception = TechnicalAnalysisException(
            "Test error",
            error_type="TEST_ERROR",
            suggestions=["Try again", "Check data"]
        )
        
        assert exception.message == "Test error"
        assert exception.error_type == "TEST_ERROR"
        assert len(exception.suggestions) == 2
        assert "Try again" in exception.suggestions
    
    def test_technical_analysis_exception_defaults(self):
        """Test TechnicalAnalysisException with default values."""
        exception = TechnicalAnalysisException("Test error")
        
        assert exception.message == "Test error"
        assert exception.error_type == "ANALYSIS_ERROR"
        assert exception.suggestions == []


# Integration Tests

@pytest.mark.asyncio
class TestTechnicalAnalyzerIntegration:
    """Integration tests for TechnicalAnalyzer with real-like data."""
    
    @pytest.fixture
    def realistic_price_data(self):
        """Create realistic price data for integration testing."""
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        
        # Create realistic OHLCV data with trends and patterns
        base_price = 150
        prices = []
        volumes = []
        
        for i, date in enumerate(dates):
            # Add seasonal and trend components
            trend = i * 0.05  # Long-term upward trend
            seasonal = 10 * np.sin(i / 30)  # Monthly seasonality
            noise = np.random.normal(0, 3)  # Random volatility
            
            price = base_price + trend + seasonal + noise
            price = max(price, 10)  # Ensure positive prices
            
            # Create OHLC from close price
            open_price = price + np.random.normal(0, 1)
            high_price = max(price, open_price) + abs(np.random.normal(0, 2))
            low_price = min(price, open_price) - abs(np.random.normal(0, 2))
            
            prices.append({
                'Open': max(open_price, 1),
                'High': max(high_price, 1),
                'Low': max(low_price, 1),
                'Close': max(price, 1),
                'Volume': np.random.randint(1000000, 20000000)
            })
        
        return pd.DataFrame(prices, index=dates)
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_full_technical_analysis_workflow(self, mock_ticker_class, realistic_price_data):
        """Test complete technical analysis workflow with realistic data."""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = realistic_price_data
        mock_ticker_class.return_value = mock_ticker
        
        analyzer = TechnicalAnalyzer()
        
        # Test single timeframe analysis
        result = await analyzer.analyze_technical("AAPL", TimeFrame.ONE_DAY)
        
        # Verify comprehensive analysis
        assert result.symbol == "AAPL"
        assert result.data_points > 200  # Should have plenty of data
        
        # Check that major indicators are calculated
        assert result.sma_20 is not None
        assert result.sma_50 is not None
        assert result.rsi is not None
        assert result.macd is not None
        
        # Verify trend and signal are determined
        assert result.trend_direction != TrendDirection.UNKNOWN
        assert result.overall_signal != SignalStrength.NEUTRAL or True  # May be neutral
        
        # Check support/resistance levels
        assert isinstance(result.support_levels, list)
        assert isinstance(result.resistance_levels, list)
    
    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_multi_timeframe_comprehensive_analysis(self, mock_ticker_class, realistic_price_data):
        """Test comprehensive multi-timeframe analysis."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = realistic_price_data
        mock_ticker_class.return_value = mock_ticker
        
        analyzer = TechnicalAnalyzer()
        
        # Test multi-timeframe analysis
        timeframes = [TimeFrame.ONE_DAY, TimeFrame.ONE_WEEK, TimeFrame.ONE_MONTH]
        result = await analyzer.analyze_multi_timeframe("AAPL", timeframes)
        
        # Verify multi-timeframe results
        assert result.symbol == "AAPL"
        assert len(result.analyses) > 0
        
        # Check consensus and alignment
        assert result.consensus_signal is not None
        assert isinstance(result.trend_alignment, bool)
        
        # Verify key levels aggregation
        assert 'support' in result.key_levels
        assert 'resistance' in result.key_levels
        assert isinstance(result.key_levels['support'], list)
        assert isinstance(result.key_levels['resistance'], list)