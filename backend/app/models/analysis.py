"""
Analysis result and recommendation models.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .fundamental import FundamentalData
from .technical import TechnicalData, SignalStrength, TrendDirection


class AnalysisType(str, Enum):
    """Types of analysis performed."""
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    COMBINED = "combined"


class Recommendation(str, Enum):
    """Investment recommendation levels."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class PriceTarget(BaseModel):
    """Price target with timeframe."""
    
    target: Decimal = Field(..., ge=0, description="Target price")
    timeframe: str = Field(..., description="Target timeframe (e.g., '3M', '6M', '1Y')")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level (0-100)")
    rationale: str = Field(..., description="Reasoning for the target")
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe format."""
        valid_timeframes = ['1M', '3M', '6M', '1Y', '2Y']
        if v not in valid_timeframes:
            raise ValueError(f'Timeframe must be one of {valid_timeframes}')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AnalysisResult(BaseModel):
    """Comprehensive analysis result."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    recommendation: Recommendation = Field(..., description="Investment recommendation")
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence level (0-100)")
    
    # Scoring
    overall_score: int = Field(..., ge=0, le=100, description="Overall analysis score (0-100)")
    fundamental_score: Optional[int] = Field(None, ge=0, le=100, description="Fundamental analysis score")
    technical_score: Optional[int] = Field(None, ge=0, le=100, description="Technical analysis score")
    
    # Analysis reasoning
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    weaknesses: List[str] = Field(default_factory=list, description="Key weaknesses identified")
    risks: List[str] = Field(default_factory=list, description="Risk factors")
    opportunities: List[str] = Field(default_factory=list, description="Opportunities identified")
    
    # Price targets
    price_targets: List[PriceTarget] = Field(default_factory=list, description="Price targets")
    
    # Risk assessment
    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    risk_factors: Dict[str, Any] = Field(default_factory=dict, description="Detailed risk factors")
    
    # Supporting data
    fundamental_data: Optional[FundamentalData] = Field(None, description="Fundamental analysis data")
    technical_data: Optional[TechnicalData] = Field(None, description="Technical analysis data")
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    data_freshness: Dict[str, datetime] = Field(default_factory=dict, description="Data source timestamps")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        return v.upper()
    
    @validator('confidence', 'overall_score', 'fundamental_score', 'technical_score')
    def validate_scores(cls, v):
        """Validate scores are within valid range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Scores must be between 0 and 100')
        return v
    
    def get_recommendation_summary(self) -> str:
        """Get a human-readable recommendation summary."""
        confidence_text = "high" if self.confidence >= 80 else "moderate" if self.confidence >= 60 else "low"
        
        summary = f"{self.recommendation.value} with {confidence_text} confidence ({self.confidence}%)"
        
        if self.price_targets:
            short_term = next((pt for pt in self.price_targets if pt.timeframe in ['1M', '3M']), None)
            if short_term:
                summary += f". Short-term target: ${short_term.target}"
        
        return summary
    
    def get_risk_summary(self) -> str:
        """Get a human-readable risk summary."""
        risk_text = {
            RiskLevel.LOW: "Low risk investment with stable fundamentals",
            RiskLevel.MODERATE: "Moderate risk with balanced risk/reward profile", 
            RiskLevel.HIGH: "High risk investment requiring careful monitoring",
            RiskLevel.VERY_HIGH: "Very high risk - suitable only for risk-tolerant investors"
        }
        
        return risk_text.get(self.risk_level, "Risk level assessment unavailable")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "analysis_type": "combined",
                "recommendation": "BUY",
                "confidence": 78,
                "overall_score": 75,
                "fundamental_score": 80,
                "technical_score": 70,
                "strengths": [
                    "Strong financial position with low debt",
                    "Consistent revenue growth",
                    "Technical indicators showing bullish momentum"
                ],
                "weaknesses": [
                    "High valuation compared to peers",
                    "Dependence on iPhone sales"
                ],
                "risks": [
                    "Market volatility",
                    "Regulatory challenges",
                    "Supply chain disruptions"
                ],
                "opportunities": [
                    "Services revenue growth",
                    "Expansion in emerging markets",
                    "New product categories"
                ],
                "price_targets": [
                    {
                        "target": 165.00,
                        "timeframe": "3M",
                        "confidence": 75,
                        "rationale": "Based on P/E expansion and earnings growth"
                    },
                    {
                        "target": 180.00,
                        "timeframe": "1Y",
                        "confidence": 65,
                        "rationale": "Long-term growth trajectory and market expansion"
                    }
                ],
                "risk_level": "MODERATE",
                "risk_factors": {
                    "volatility": 0.25,
                    "beta": 1.2,
                    "debt_ratio": 0.3
                },
                "analysis_timestamp": "2024-01-15T15:30:00Z",
                "data_freshness": {
                    "fundamental": "2024-01-15T10:00:00Z",
                    "technical": "2024-01-15T15:25:00Z"
                }
            }
        }


class CombinedAnalysis(BaseModel):
    """Combined fundamental and technical analysis data."""
    
    symbol: str = Field(..., description="Stock ticker symbol")
    fundamental_analysis: Optional[FundamentalData] = Field(None, description="Fundamental analysis results")
    technical_analysis: Optional[TechnicalData] = Field(None, description="Technical analysis results")
    market_data: Optional[Dict[str, Any]] = Field(None, description="Current market data")
    
    # Analysis alignment
    fundamental_signal: Optional[str] = Field(None, description="Fundamental analysis signal")
    technical_signal: Optional[SignalStrength] = Field(None, description="Technical analysis signal")
    signals_aligned: bool = Field(default=False, description="Whether fundamental and technical signals align")
    
    # Combined metrics
    combined_score: Optional[int] = Field(None, ge=0, le=100, description="Combined analysis score")
    conviction_level: Optional[str] = Field(None, description="Conviction level based on signal alignment")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        return v.upper()
    
    def calculate_signal_alignment(self) -> bool:
        """Calculate whether fundamental and technical signals are aligned."""
        if not self.fundamental_signal or not self.technical_signal:
            return False
        
        # Map signals to numeric values for comparison
        fundamental_map = {
            'strong_buy': 2, 'buy': 1, 'hold': 0, 'sell': -1, 'strong_sell': -2
        }
        
        technical_map = {
            SignalStrength.STRONG_BUY: 2,
            SignalStrength.BUY: 1,
            SignalStrength.WEAK_BUY: 0.5,
            SignalStrength.NEUTRAL: 0,
            SignalStrength.WEAK_SELL: -0.5,
            SignalStrength.SELL: -1,
            SignalStrength.STRONG_SELL: -2
        }
        
        fund_value = fundamental_map.get(self.fundamental_signal.lower(), 0)
        tech_value = technical_map.get(self.technical_signal, 0)
        
        # Consider aligned if both are positive, both negative, or both neutral
        return (fund_value > 0 and tech_value > 0) or \
               (fund_value < 0 and tech_value < 0) or \
               (abs(fund_value) <= 0.5 and abs(tech_value) <= 0.5)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }