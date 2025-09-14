"""
Technical analysis data models.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TimeFrame(str, Enum):
    """Supported timeframes for technical analysis."""
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    TWO_YEARS = "2Y"


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class SignalStrength(str, Enum):
    """Signal strength levels."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class TechnicalIndicator(BaseModel):
    """Individual technical indicator data."""
    
    name: str = Field(..., description="Indicator name (e.g., SMA, RSI, MACD)")
    value: Optional[Decimal] = Field(None, description="Current indicator value")
    signal: SignalStrength = Field(default=SignalStrength.NEUTRAL, description="Signal strength")
    period: Optional[int] = Field(None, ge=1, description="Period used for calculation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate indicator name."""
        valid_indicators = [
            'SMA', 'EMA', 'RSI', 'MACD', 'MACD_SIGNAL', 'MACD_HISTOGRAM',
            'BOLLINGER_UPPER', 'BOLLINGER_LOWER', 'BOLLINGER_MIDDLE',
            'STOCHASTIC_K', 'STOCHASTIC_D', 'ADX', 'CCI', 'WILLIAMS_R',
            'MOMENTUM', 'ROC', 'ATR', 'OBV'
        ]
        if v.upper() not in valid_indicators:
            raise ValueError(f'Indicator name must be one of {valid_indicators}')
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class SupportResistanceLevel(BaseModel):
    """Support or resistance level data."""
    
    level: Decimal = Field(..., ge=0, description="Price level")
    strength: int = Field(..., ge=1, le=10, description="Strength of the level (1-10)")
    type: str = Field(..., description="Type: 'support' or 'resistance'")
    touches: int = Field(default=1, ge=1, description="Number of times price touched this level")
    last_touch: Optional[datetime] = Field(None, description="Last time price touched this level")
    
    @validator('type')
    def validate_type(cls, v):
        """Validate level type."""
        if v.lower() not in ['support', 'resistance']:
            raise ValueError('Type must be either "support" or "resistance"')
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class TechnicalData(BaseModel):
    """Complete technical analysis data model."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    timeframe: TimeFrame = Field(..., description="Analysis timeframe")
    
    # Moving Averages
    sma_20: Optional[Decimal] = Field(None, description="20-period Simple Moving Average")
    sma_50: Optional[Decimal] = Field(None, description="50-period Simple Moving Average")
    sma_200: Optional[Decimal] = Field(None, description="200-period Simple Moving Average")
    ema_12: Optional[Decimal] = Field(None, description="12-period Exponential Moving Average")
    ema_26: Optional[Decimal] = Field(None, description="26-period Exponential Moving Average")
    
    # Momentum Indicators
    rsi: Optional[Decimal] = Field(None, ge=0, le=100, description="Relative Strength Index")
    macd: Optional[Decimal] = Field(None, description="MACD line")
    macd_signal: Optional[Decimal] = Field(None, description="MACD signal line")
    macd_histogram: Optional[Decimal] = Field(None, description="MACD histogram")
    
    # Bollinger Bands
    bollinger_upper: Optional[Decimal] = Field(None, description="Bollinger Bands upper band")
    bollinger_lower: Optional[Decimal] = Field(None, description="Bollinger Bands lower band")
    bollinger_middle: Optional[Decimal] = Field(None, description="Bollinger Bands middle band")
    
    # Volume Indicators
    volume_sma: Optional[int] = Field(None, ge=0, description="Volume Simple Moving Average")
    obv: Optional[int] = Field(None, description="On-Balance Volume")
    
    # Volatility
    atr: Optional[Decimal] = Field(None, ge=0, description="Average True Range")
    
    # Support and Resistance
    support_levels: List[SupportResistanceLevel] = Field(default_factory=list, description="Support levels")
    resistance_levels: List[SupportResistanceLevel] = Field(default_factory=list, description="Resistance levels")
    
    # Overall Analysis
    trend_direction: TrendDirection = Field(default=TrendDirection.UNKNOWN, description="Overall trend direction")
    overall_signal: SignalStrength = Field(default=SignalStrength.NEUTRAL, description="Overall technical signal")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    data_points: int = Field(default=0, ge=0, description="Number of data points used in analysis")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        return v.upper()
    
    @validator('rsi')
    def validate_rsi(cls, v):
        """Validate RSI is within valid range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('RSI must be between 0 and 100')
        return v
    
    def get_all_indicators(self) -> List[TechnicalIndicator]:
        """Get all indicators as a list of TechnicalIndicator objects."""
        indicators = []
        
        # Moving averages
        if self.sma_20:
            indicators.append(TechnicalIndicator(name="SMA", value=self.sma_20, period=20))
        if self.sma_50:
            indicators.append(TechnicalIndicator(name="SMA", value=self.sma_50, period=50))
        if self.sma_200:
            indicators.append(TechnicalIndicator(name="SMA", value=self.sma_200, period=200))
        if self.ema_12:
            indicators.append(TechnicalIndicator(name="EMA", value=self.ema_12, period=12))
        if self.ema_26:
            indicators.append(TechnicalIndicator(name="EMA", value=self.ema_26, period=26))
        
        # Momentum indicators
        if self.rsi:
            signal = SignalStrength.NEUTRAL
            if self.rsi > 70:
                signal = SignalStrength.SELL
            elif self.rsi < 30:
                signal = SignalStrength.BUY
            indicators.append(TechnicalIndicator(name="RSI", value=self.rsi, signal=signal, period=14))
        
        if self.macd:
            indicators.append(TechnicalIndicator(name="MACD", value=self.macd))
        if self.macd_signal:
            indicators.append(TechnicalIndicator(name="MACD_SIGNAL", value=self.macd_signal))
        
        # Bollinger Bands
        if self.bollinger_upper:
            indicators.append(TechnicalIndicator(name="BOLLINGER_UPPER", value=self.bollinger_upper))
        if self.bollinger_lower:
            indicators.append(TechnicalIndicator(name="BOLLINGER_LOWER", value=self.bollinger_lower))
        
        return indicators
    
    def calculate_technical_score(self, current_price: Decimal) -> int:
        """Calculate overall technical score (0-100) based on indicators."""
        score = 50  # Base neutral score
        signals = 0
        
        # RSI scoring
        if self.rsi:
            if self.rsi < 30:  # Oversold - bullish
                score += 15
                signals += 1
            elif self.rsi > 70:  # Overbought - bearish
                score -= 15
                signals += 1
            elif 40 <= self.rsi <= 60:  # Neutral zone
                score += 5
                signals += 1
        
        # Moving average scoring
        if self.sma_20 and self.sma_50:
            if self.sma_20 > self.sma_50:  # Golden cross territory
                score += 10
            else:  # Death cross territory
                score -= 10
            signals += 1
        
        # Price vs moving averages
        if current_price and self.sma_20:
            if current_price > self.sma_20:
                score += 5
            else:
                score -= 5
            signals += 1
        
        # MACD scoring
        if self.macd and self.macd_signal:
            if self.macd > self.macd_signal:  # Bullish
                score += 10
            else:  # Bearish
                score -= 10
            signals += 1
        
        # Bollinger Bands scoring
        if current_price and self.bollinger_upper and self.bollinger_lower:
            bb_position = (current_price - self.bollinger_lower) / (self.bollinger_upper - self.bollinger_lower)
            if bb_position < 0.2:  # Near lower band - oversold
                score += 10
            elif bb_position > 0.8:  # Near upper band - overbought
                score -= 10
            signals += 1
        
        # If no signals available, return neutral
        if signals == 0:
            return 50
        
        return max(0, min(100, score))
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "timeframe": "1D",
                "sma_20": 148.50,
                "sma_50": 145.20,
                "sma_200": 140.80,
                "ema_12": 149.10,
                "ema_26": 147.30,
                "rsi": 65.5,
                "macd": 1.25,
                "macd_signal": 0.85,
                "macd_histogram": 0.40,
                "bollinger_upper": 152.00,
                "bollinger_lower": 144.00,
                "bollinger_middle": 148.00,
                "volume_sma": 75000000,
                "obv": 1250000000,
                "atr": 2.45,
                "support_levels": [
                    {
                        "level": 145.00,
                        "strength": 8,
                        "type": "support",
                        "touches": 3,
                        "last_touch": "2024-01-10T14:30:00Z"
                    }
                ],
                "resistance_levels": [
                    {
                        "level": 155.00,
                        "strength": 7,
                        "type": "resistance",
                        "touches": 2,
                        "last_touch": "2024-01-12T11:15:00Z"
                    }
                ],
                "trend_direction": "bullish",
                "overall_signal": "buy",
                "timestamp": "2024-01-15T15:30:00Z",
                "data_points": 252
            }
        }