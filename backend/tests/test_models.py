"""
Unit tests for data models validation and serialization.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from app.models import (
    Stock, MarketData, FundamentalData, TechnicalData,
    TechnicalIndicator, SupportResistanceLevel,
    TimeFrame, TrendDirection, SignalStrength
)


class TestStockModel:
    """Test cases for Stock model."""
    
    def test_valid_stock_creation(self):
        """Test creating a valid stock instance."""
        stock = Stock(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000
        )
        
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.exchange == "NASDAQ"
        assert stock.sector == "Technology"
        assert stock.industry == "Consumer Electronics"
        assert stock.market_cap == 3000000000000
        assert isinstance(stock.last_updated, datetime)
    
    def test_symbol_validation(self):
        """Test stock symbol validation."""
        # Valid symbols
        stock1 = Stock(symbol="AAPL", name="Apple", exchange="NASDAQ")
        assert stock1.symbol == "AAPL"
        
        stock2 = Stock(symbol="brk.a", name="Berkshire", exchange="NYSE")
        assert stock2.symbol == "BRK.A"
        
        # Invalid symbols
        with pytest.raises(ValidationError):
            Stock(symbol="", name="Test", exchange="NYSE")
        
        with pytest.raises(ValidationError):
            Stock(symbol="AAPL123", name="Test", exchange="NYSE")
    
    def test_negative_market_cap_validation(self):
        """Test that negative market cap raises validation error."""
        with pytest.raises(ValidationError):
            Stock(
                symbol="TEST",
                name="Test Company",
                exchange="NYSE",
                market_cap=-1000000
            )
    
    def test_json_serialization(self):
        """Test JSON serialization of Stock model."""
        stock = Stock(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ"
        )
        
        json_data = stock.dict()
        assert json_data["symbol"] == "AAPL"
        assert json_data["name"] == "Apple Inc."
        assert json_data["exchange"] == "NASDAQ"
        assert "last_updated" in json_data


class TestMarketDataModel:
    """Test cases for MarketData model."""
    
    def test_valid_market_data_creation(self):
        """Test creating valid market data."""
        market_data = MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00")
        )
        
        assert market_data.symbol == "AAPL"
        assert market_data.price == Decimal("150.25")
        assert market_data.change == Decimal("2.50")
        assert market_data.change_percent == Decimal("1.69")
        assert market_data.volume == 75000000
        assert not market_data.is_stale
    
    def test_negative_price_validation(self):
        """Test that negative prices raise validation errors."""
        with pytest.raises(ValidationError):
            MarketData(
                symbol="TEST",
                price=Decimal("-10.00"),
                change=Decimal("0"),
                change_percent=Decimal("0"),
                volume=1000
            )
    
    def test_extreme_change_percent_validation(self):
        """Test validation of extreme change percentages."""
        with pytest.raises(ValidationError):
            MarketData(
                symbol="TEST",
                price=Decimal("100.00"),
                change=Decimal("-150.00"),
                change_percent=Decimal("-150.00"),  # More than -100%
                volume=1000
            )
    
    def test_from_yfinance_method(self):
        """Test creating MarketData from yfinance data."""
        yf_data = {
            'symbol': 'AAPL',
            'currentPrice': 150.25,
            'regularMarketChange': 2.50,
            'regularMarketChangePercent': 1.69,
            'volume': 75000000,
            'fiftyTwoWeekHigh': 180.00,
            'fiftyTwoWeekLow': 120.00,
            'averageVolume': 80000000,
            'marketCap': 2500000000000,
            'trailingPE': 25.5
        }
        
        market_data = MarketData.from_yfinance(yf_data)
        
        assert market_data.symbol == 'AAPL'
        assert market_data.price == Decimal('150.25')
        assert market_data.change == Decimal('2.50')
        assert market_data.volume == 75000000
        assert market_data.pe_ratio == Decimal('25.5')
    
    def test_symbol_case_normalization(self):
        """Test that symbols are normalized to uppercase."""
        market_data = MarketData(
            symbol="aapl",
            price=Decimal("150.00"),
            change=Decimal("0"),
            change_percent=Decimal("0"),
            volume=1000
        )
        
        assert market_data.symbol == "AAPL"


class TestFundamentalDataModel:
    """Test cases for FundamentalData model."""
    
    def test_valid_fundamental_data_creation(self):
        """Test creating valid fundamental data."""
        fundamental = FundamentalData(
            symbol="AAPL",
            pe_ratio=Decimal("25.5"),
            pb_ratio=Decimal("8.2"),
            roe=Decimal("0.28"),
            debt_to_equity=Decimal("0.45"),
            revenue_growth=Decimal("0.08"),
            profit_margin=Decimal("0.23"),
            eps=Decimal("6.15"),
            dividend=Decimal("0.92"),
            dividend_yield=Decimal("0.006"),
            quarter="Q4",
            year=2024
        )
        
        assert fundamental.symbol == "AAPL"
        assert fundamental.pe_ratio == Decimal("25.5")
        assert fundamental.quarter == "Q4"
        assert fundamental.year == 2024
    
    def test_negative_ratios_validation(self):
        """Test that negative financial ratios raise validation errors."""
        with pytest.raises(ValidationError):
            FundamentalData(
                symbol="TEST",
                pe_ratio=Decimal("-5.0"),  # Negative PE ratio
                quarter="Q1",
                year=2024
            )
    
    def test_invalid_quarter_validation(self):
        """Test quarter validation."""
        with pytest.raises(ValidationError):
            FundamentalData(
                symbol="TEST",
                quarter="Q5",  # Invalid quarter
                year=2024
            )
    
    def test_extreme_dividend_yield_validation(self):
        """Test validation of unreasonably high dividend yields."""
        with pytest.raises(ValidationError):
            FundamentalData(
                symbol="TEST",
                dividend_yield=Decimal("0.75"),  # 75% yield is unreasonable
                quarter="Q1",
                year=2024
            )
    
    def test_health_score_calculation(self):
        """Test financial health score calculation."""
        # Strong company
        strong_fundamental = FundamentalData(
            symbol="STRONG",
            pe_ratio=Decimal("15.0"),
            roe=Decimal("0.20"),
            debt_to_equity=Decimal("0.25"),
            profit_margin=Decimal("0.25"),
            quarter="Q4",
            year=2024
        )
        
        score = strong_fundamental.calculate_health_score()
        assert score is not None
        assert score > 70  # Should be a high score
        
        # Weak company
        weak_fundamental = FundamentalData(
            symbol="WEAK",
            pe_ratio=Decimal("50.0"),
            roe=Decimal("0.02"),
            debt_to_equity=Decimal("2.0"),
            profit_margin=Decimal("-0.05"),
            quarter="Q4",
            year=2024
        )
        
        score = weak_fundamental.calculate_health_score()
        assert score is not None
        assert score < 40  # Should be a low score
    
    def test_from_yfinance_method(self):
        """Test creating FundamentalData from yfinance data."""
        yf_data = {
            'trailingPE': 25.5,
            'priceToBook': 8.2,
            'returnOnEquity': 0.28,
            'debtToEquity': 0.45,
            'revenueGrowth': 0.08,
            'profitMargins': 0.23,
            'trailingEps': 6.15,
            'dividendRate': 0.92,
            'dividendYield': 0.006
        }
        
        fundamental = FundamentalData.from_yfinance(yf_data, "AAPL")
        
        assert fundamental.symbol == "AAPL"
        assert fundamental.pe_ratio == Decimal("25.5")
        assert fundamental.roe == Decimal("0.28")


class TestTechnicalDataModel:
    """Test cases for TechnicalData model."""
    
    def test_valid_technical_data_creation(self):
        """Test creating valid technical data."""
        support_level = SupportResistanceLevel(
            level=Decimal("145.00"),
            strength=8,
            type="support",
            touches=3
        )
        
        resistance_level = SupportResistanceLevel(
            level=Decimal("155.00"),
            strength=7,
            type="resistance",
            touches=2
        )
        
        technical = TechnicalData(
            symbol="AAPL",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("148.50"),
            sma_50=Decimal("145.20"),
            rsi=Decimal("65.5"),
            macd=Decimal("1.25"),
            macd_signal=Decimal("0.85"),
            support_levels=[support_level],
            resistance_levels=[resistance_level],
            trend_direction=TrendDirection.BULLISH,
            overall_signal=SignalStrength.BUY,
            data_points=252
        )
        
        assert technical.symbol == "AAPL"
        assert technical.timeframe == TimeFrame.ONE_DAY
        assert technical.rsi == Decimal("65.5")
        assert len(technical.support_levels) == 1
        assert len(technical.resistance_levels) == 1
        assert technical.trend_direction == TrendDirection.BULLISH
    
    def test_rsi_range_validation(self):
        """Test RSI validation within 0-100 range."""
        with pytest.raises(ValidationError):
            TechnicalData(
                symbol="TEST",
                timeframe=TimeFrame.ONE_DAY,
                rsi=Decimal("150.0")  # RSI cannot be > 100
            )
        
        with pytest.raises(ValidationError):
            TechnicalData(
                symbol="TEST",
                timeframe=TimeFrame.ONE_DAY,
                rsi=Decimal("-10.0")  # RSI cannot be < 0
            )
    
    def test_get_all_indicators_method(self):
        """Test getting all indicators as TechnicalIndicator objects."""
        technical = TechnicalData(
            symbol="AAPL",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("148.50"),
            rsi=Decimal("75.0"),  # Overbought
            macd=Decimal("1.25")
        )
        
        indicators = technical.get_all_indicators()
        
        assert len(indicators) >= 3
        
        # Check RSI signal is correctly set to SELL (overbought)
        rsi_indicator = next((ind for ind in indicators if ind.name == "RSI"), None)
        assert rsi_indicator is not None
        assert rsi_indicator.signal == SignalStrength.SELL
        assert rsi_indicator.value == Decimal("75.0")
    
    def test_technical_score_calculation(self):
        """Test technical score calculation."""
        # Bullish setup
        bullish_technical = TechnicalData(
            symbol="BULL",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("150.00"),
            sma_50=Decimal("145.00"),  # SMA20 > SMA50 (bullish)
            rsi=Decimal("25.0"),  # Oversold (bullish)
            macd=Decimal("1.25"),
            macd_signal=Decimal("0.85"),  # MACD > Signal (bullish)
            bollinger_upper=Decimal("155.00"),
            bollinger_lower=Decimal("140.00")
        )
        
        current_price = Decimal("152.00")
        score = bullish_technical.calculate_technical_score(current_price)
        assert score > 60  # Should be bullish score
        
        # Bearish setup
        bearish_technical = TechnicalData(
            symbol="BEAR",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("145.00"),
            sma_50=Decimal("150.00"),  # SMA20 < SMA50 (bearish)
            rsi=Decimal("80.0"),  # Overbought (bearish)
            macd=Decimal("0.85"),
            macd_signal=Decimal("1.25"),  # MACD < Signal (bearish)
            bollinger_upper=Decimal("155.00"),
            bollinger_lower=Decimal("140.00")
        )
        
        current_price = Decimal("142.00")
        score = bearish_technical.calculate_technical_score(current_price)
        assert score < 40  # Should be bearish score


class TestSupportResistanceLevelModel:
    """Test cases for SupportResistanceLevel model."""
    
    def test_valid_support_resistance_creation(self):
        """Test creating valid support/resistance levels."""
        support = SupportResistanceLevel(
            level=Decimal("145.00"),
            strength=8,
            type="support",
            touches=3,
            last_touch=datetime.now()
        )
        
        assert support.level == Decimal("145.00")
        assert support.strength == 8
        assert support.type == "support"
        assert support.touches == 3
        
        resistance = SupportResistanceLevel(
            level=Decimal("155.00"),
            strength=7,
            type="resistance",
            touches=2
        )
        
        assert resistance.type == "resistance"
    
    def test_invalid_type_validation(self):
        """Test validation of support/resistance type."""
        with pytest.raises(ValidationError):
            SupportResistanceLevel(
                level=Decimal("145.00"),
                strength=5,
                type="invalid_type",
                touches=1
            )
    
    def test_strength_range_validation(self):
        """Test strength validation within 1-10 range."""
        with pytest.raises(ValidationError):
            SupportResistanceLevel(
                level=Decimal("145.00"),
                strength=0,  # Below minimum
                type="support",
                touches=1
            )
        
        with pytest.raises(ValidationError):
            SupportResistanceLevel(
                level=Decimal("145.00"),
                strength=11,  # Above maximum
                type="support",
                touches=1
            )


class TestTechnicalIndicatorModel:
    """Test cases for TechnicalIndicator model."""
    
    def test_valid_indicator_creation(self):
        """Test creating valid technical indicators."""
        indicator = TechnicalIndicator(
            name="RSI",
            value=Decimal("65.5"),
            signal=SignalStrength.NEUTRAL,
            period=14
        )
        
        assert indicator.name == "RSI"
        assert indicator.value == Decimal("65.5")
        assert indicator.signal == SignalStrength.NEUTRAL
        assert indicator.period == 14
    
    def test_indicator_name_validation(self):
        """Test validation of indicator names."""
        # Valid indicator
        indicator = TechnicalIndicator(name="SMA", signal=SignalStrength.NEUTRAL)
        assert indicator.name == "SMA"
        
        # Invalid indicator
        with pytest.raises(ValidationError):
            TechnicalIndicator(name="INVALID_INDICATOR", signal=SignalStrength.NEUTRAL)
    
    def test_case_insensitive_name_validation(self):
        """Test that indicator names are case-insensitive."""
        indicator = TechnicalIndicator(name="rsi", signal=SignalStrength.NEUTRAL)
        assert indicator.name == "RSI"


class TestEnumValidation:
    """Test cases for enum validation."""
    
    def test_timeframe_enum(self):
        """Test TimeFrame enum values."""
        assert TimeFrame.ONE_DAY == "1D"
        assert TimeFrame.ONE_WEEK == "1W"
        assert TimeFrame.ONE_MONTH == "1M"
        assert TimeFrame.ONE_YEAR == "1Y"
    
    def test_trend_direction_enum(self):
        """Test TrendDirection enum values."""
        assert TrendDirection.BULLISH == "bullish"
        assert TrendDirection.BEARISH == "bearish"
        assert TrendDirection.SIDEWAYS == "sideways"
        assert TrendDirection.UNKNOWN == "unknown"
    
    def test_signal_strength_enum(self):
        """Test SignalStrength enum values."""
        assert SignalStrength.STRONG_BUY == "strong_buy"
        assert SignalStrength.BUY == "buy"
        assert SignalStrength.NEUTRAL == "neutral"
        assert SignalStrength.SELL == "sell"
        assert SignalStrength.STRONG_SELL == "strong_sell"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_string_validation(self):
        """Test validation with empty strings."""
        with pytest.raises(ValidationError):
            Stock(symbol="", name="Test", exchange="NYSE")
        
        with pytest.raises(ValidationError):
            MarketData(
                symbol="",
                price=Decimal("100"),
                change=Decimal("0"),
                change_percent=Decimal("0"),
                volume=1000
            )
    
    def test_none_values_handling(self):
        """Test handling of None values for optional fields."""
        market_data = MarketData(
            symbol="TEST",
            price=Decimal("100.00"),
            change=Decimal("0"),
            change_percent=Decimal("0"),
            volume=1000,
            high_52_week=None,
            low_52_week=None,
            pe_ratio=None
        )
        
        assert market_data.high_52_week is None
        assert market_data.low_52_week is None
        assert market_data.pe_ratio is None
    
    def test_large_numbers_handling(self):
        """Test handling of very large numbers."""
        stock = Stock(
            symbol="LARGE",
            name="Large Company",
            exchange="NYSE",
            market_cap=999999999999999  # Very large market cap
        )
        
        assert stock.market_cap == 999999999999999
    
    def test_decimal_precision(self):
        """Test decimal precision handling."""
        market_data = MarketData(
            symbol="PRECISE",
            price=Decimal("123.456789"),
            change=Decimal("0.123456"),
            change_percent=Decimal("0.001234"),
            volume=1000
        )
        
        # Decimals should maintain precision
        assert str(market_data.price) == "123.456789"
        assert str(market_data.change) == "0.123456"