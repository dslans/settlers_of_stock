"""
Fundamental analysis data models.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class FundamentalData(BaseModel):
    """Fundamental analysis data model."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    pe_ratio: Optional[Decimal] = Field(None, description="Price-to-earnings ratio")
    pb_ratio: Optional[Decimal] = Field(None, description="Price-to-book ratio")
    roe: Optional[Decimal] = Field(None, description="Return on equity")
    debt_to_equity: Optional[Decimal] = Field(None, ge=0, description="Debt-to-equity ratio")
    revenue_growth: Optional[Decimal] = Field(None, description="Revenue growth rate")
    profit_margin: Optional[Decimal] = Field(None, description="Profit margin")
    eps: Optional[Decimal] = Field(None, description="Earnings per share")
    dividend: Optional[Decimal] = Field(None, ge=0, description="Dividend per share")
    dividend_yield: Optional[Decimal] = Field(None, ge=0, le=1, description="Dividend yield as decimal")
    book_value: Optional[Decimal] = Field(None, description="Book value per share")
    revenue: Optional[int] = Field(None, description="Total revenue")
    net_income: Optional[int] = Field(None, description="Net income")
    total_debt: Optional[int] = Field(None, ge=0, description="Total debt")
    total_equity: Optional[int] = Field(None, description="Total equity")
    free_cash_flow: Optional[int] = Field(None, description="Free cash flow")
    quarter: str = Field(..., description="Quarter (e.g., Q1, Q2, Q3, Q4)")
    year: int = Field(..., ge=1900, le=2100, description="Year")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        return v.upper()
    
    @validator('pe_ratio', 'pb_ratio')
    def validate_ratios(cls, v):
        """Validate financial ratios are reasonable."""
        if v is not None and v < 0:
            raise ValueError('Financial ratios cannot be negative')
        return v
    
    @validator('roe', 'revenue_growth', 'profit_margin')
    def validate_percentages(cls, v):
        """Validate percentage fields are reasonable."""
        if v is not None and (v < -1 or v > 10):  # Allow -100% to 1000%
            raise ValueError('Percentage values must be between -1 and 10')
        return v
    
    @validator('quarter')
    def validate_quarter(cls, v):
        """Validate quarter format."""
        valid_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        if v not in valid_quarters:
            raise ValueError(f'Quarter must be one of {valid_quarters}')
        return v
    
    @validator('dividend_yield')
    def validate_dividend_yield(cls, v):
        """Validate dividend yield is reasonable."""
        if v is not None and v > 0.5:  # More than 50% yield is suspicious
            raise ValueError('Dividend yield seems unreasonably high')
        return v
    
    @classmethod
    def from_yfinance(cls, yf_data: Dict[str, Any], symbol: str) -> 'FundamentalData':
        """Create FundamentalData from yfinance ticker info."""
        return cls(
            symbol=symbol,
            pe_ratio=Decimal(str(yf_data.get('trailingPE'))) if yf_data.get('trailingPE') else None,
            pb_ratio=Decimal(str(yf_data.get('priceToBook'))) if yf_data.get('priceToBook') else None,
            roe=Decimal(str(yf_data.get('returnOnEquity'))) if yf_data.get('returnOnEquity') else None,
            debt_to_equity=Decimal(str(yf_data.get('debtToEquity'))) if yf_data.get('debtToEquity') else None,
            revenue_growth=Decimal(str(yf_data.get('revenueGrowth'))) if yf_data.get('revenueGrowth') else None,
            profit_margin=Decimal(str(yf_data.get('profitMargins'))) if yf_data.get('profitMargins') else None,
            eps=Decimal(str(yf_data.get('trailingEps'))) if yf_data.get('trailingEps') else None,
            dividend=Decimal(str(yf_data.get('dividendRate'))) if yf_data.get('dividendRate') else None,
            dividend_yield=Decimal(str(yf_data.get('dividendYield'))) if yf_data.get('dividendYield') else None,
            book_value=Decimal(str(yf_data.get('bookValue'))) if yf_data.get('bookValue') else None,
            revenue=yf_data.get('totalRevenue'),
            net_income=yf_data.get('netIncomeToCommon'),
            total_debt=yf_data.get('totalDebt'),
            total_equity=yf_data.get('totalStockholderEquity'),
            free_cash_flow=yf_data.get('freeCashflow'),
            quarter="Q4",  # Default, should be determined from actual data
            year=datetime.now().year
        )
    
    def calculate_health_score(self) -> Optional[int]:
        """Calculate a simple financial health score (0-100)."""
        if not any([self.pe_ratio, self.pb_ratio, self.roe, self.debt_to_equity]):
            return None
        
        score = 50  # Base score
        
        # PE ratio scoring (lower is better, but not too low)
        if self.pe_ratio:
            if 10 <= self.pe_ratio <= 25:
                score += 15
            elif 5 <= self.pe_ratio < 10 or 25 < self.pe_ratio <= 35:
                score += 10
            elif self.pe_ratio > 35:
                score -= 10
        
        # ROE scoring (higher is better)
        if self.roe:
            if self.roe >= 0.15:  # 15% or higher
                score += 15
            elif self.roe >= 0.10:  # 10-15%
                score += 10
            elif self.roe >= 0.05:  # 5-10%
                score += 5
            else:
                score -= 10
        
        # Debt-to-equity scoring (lower is better)
        if self.debt_to_equity:
            if self.debt_to_equity <= 0.3:
                score += 10
            elif self.debt_to_equity <= 0.6:
                score += 5
            elif self.debt_to_equity > 1.0:
                score -= 15
        
        # Profit margin scoring
        if self.profit_margin:
            if self.profit_margin >= 0.20:  # 20% or higher
                score += 10
            elif self.profit_margin >= 0.10:  # 10-20%
                score += 5
            elif self.profit_margin < 0:  # Negative margins
                score -= 20
        
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
                "pe_ratio": 25.5,
                "pb_ratio": 8.2,
                "roe": 0.28,
                "debt_to_equity": 0.45,
                "revenue_growth": 0.08,
                "profit_margin": 0.23,
                "eps": 6.15,
                "dividend": 0.92,
                "dividend_yield": 0.006,
                "book_value": 18.5,
                "revenue": 394328000000,
                "net_income": 99803000000,
                "total_debt": 132480000000,
                "total_equity": 62146000000,
                "free_cash_flow": 84726000000,
                "quarter": "Q4",
                "year": 2024,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }