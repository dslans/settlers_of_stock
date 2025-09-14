"""
Fundamental Analysis Engine for stock analysis.
Provides comprehensive fundamental analysis including financial ratios,
company health assessment, and industry comparisons.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

from ..models.fundamental import FundamentalData
from ..models.stock import Stock
from .data_aggregation import DataAggregationService, DataAggregationException


# Configure logging
logger = logging.getLogger(__name__)


class HealthRating(str, Enum):
    """Company health rating categories."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"


class CompanyHealth(BaseModel):
    """Company health assessment result."""
    symbol: str
    overall_score: int  # 0-100
    rating: HealthRating
    strengths: List[str]
    weaknesses: List[str]
    key_metrics: Dict[str, Any]
    assessment_date: datetime


class IndustryComparison(BaseModel):
    """Industry comparison result."""
    symbol: str
    industry: str
    sector: str
    peer_symbols: List[str]
    percentile_rankings: Dict[str, float]  # metric -> percentile (0-100)
    industry_averages: Dict[str, float]
    relative_performance: Dict[str, str]  # metric -> "Above/Below/At Average"


class FundamentalAnalysisException(Exception):
    """Custom exception for fundamental analysis errors."""
    
    def __init__(self, message: str, error_type: str = "ANALYSIS_ERROR", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class FundamentalAnalyzer:
    """
    Comprehensive fundamental analysis engine.
    
    Provides financial ratio calculations, company health assessment,
    and industry comparison functionality.
    """
    
    def __init__(self, data_service: Optional[DataAggregationService] = None):
        """Initialize the fundamental analyzer."""
        self.data_service = data_service or DataAggregationService()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Industry peer mapping (simplified for demo - in production would use comprehensive database)
        self.industry_peers = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "NFLX", "ADBE"],
            "Financial Services": ["JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BLK"],
            "Healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "ABT", "LLY"],
            "Consumer Cyclical": ["AMZN", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "F"],
            "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST", "CL", "KMB", "GIS"],
            "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC"],
            "Industrials": ["BA", "CAT", "GE", "MMM", "HON", "UPS", "RTX", "LMT"],
            "Materials": ["LIN", "APD", "SHW", "ECL", "FCX", "NEM", "DOW", "DD"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "EXR", "AVB", "EQR"],
            "Utilities": ["NEE", "SO", "DUK", "AEP", "EXC", "XEL", "ED", "ETR"],
            "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "CHTR"]
        }
    
    async def analyze_fundamentals(self, symbol: str) -> FundamentalData:
        """
        Perform comprehensive fundamental analysis for a stock.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            FundamentalData with calculated ratios and metrics
            
        Raises:
            FundamentalAnalysisException: If analysis cannot be performed
        """
        symbol = symbol.upper().strip()
        
        try:
            # Fetch fundamental data using yfinance
            fundamental_data = await self._fetch_fundamental_data(symbol)
            
            # Calculate additional ratios if raw data is available
            enhanced_data = await self._enhance_fundamental_data(fundamental_data)
            
            logger.info(f"Successfully analyzed fundamentals for {symbol}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Failed to analyze fundamentals for {symbol}: {e}")
            raise FundamentalAnalysisException(
                f"Unable to perform fundamental analysis for {symbol}: {str(e)}",
                error_type="DATA_ERROR",
                suggestions=[
                    "Verify symbol exists and is publicly traded",
                    "Check if company has recent financial filings",
                    "Try again later if data source is temporarily unavailable"
                ]
            )
    
    async def assess_company_health(self, symbol: str) -> CompanyHealth:
        """
        Assess overall company financial health.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            CompanyHealth assessment with score and detailed analysis
        """
        try:
            fundamental_data = await self.analyze_fundamentals(symbol)
            
            # Calculate health score and assessment
            score, strengths, weaknesses, key_metrics = self._calculate_health_score(fundamental_data)
            
            # Determine rating based on score
            if score >= 80:
                rating = HealthRating.EXCELLENT
            elif score >= 65:
                rating = HealthRating.GOOD
            elif score >= 50:
                rating = HealthRating.FAIR
            elif score >= 30:
                rating = HealthRating.POOR
            else:
                rating = HealthRating.CRITICAL
            
            return CompanyHealth(
                symbol=symbol,
                overall_score=score,
                rating=rating,
                strengths=strengths,
                weaknesses=weaknesses,
                key_metrics=key_metrics,
                assessment_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to assess company health for {symbol}: {e}")
            raise FundamentalAnalysisException(
                f"Unable to assess company health for {symbol}: {str(e)}",
                error_type="ASSESSMENT_ERROR"
            )
    
    async def compare_to_industry(self, symbol: str) -> IndustryComparison:
        """
        Compare stock's fundamentals to industry peers.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            IndustryComparison with peer analysis and rankings
        """
        try:
            # Get stock info to determine industry
            stock_info = await self.data_service.get_stock_info(symbol)
            industry = stock_info.sector or "Technology"  # Default fallback
            
            # Get peer symbols for the industry
            peer_symbols = self.industry_peers.get(industry, [])
            if symbol.upper() not in peer_symbols:
                peer_symbols.append(symbol.upper())
            
            # Fetch fundamental data for all peers
            peer_data = await self._fetch_peer_fundamentals(peer_symbols)
            
            # Calculate industry averages and percentile rankings
            industry_averages = self._calculate_industry_averages(peer_data)
            percentile_rankings = self._calculate_percentile_rankings(symbol, peer_data)
            relative_performance = self._determine_relative_performance(
                symbol, peer_data, industry_averages
            )
            
            return IndustryComparison(
                symbol=symbol,
                industry=industry,
                sector=stock_info.sector or "Unknown",
                peer_symbols=[s for s in peer_symbols if s != symbol.upper()],
                percentile_rankings=percentile_rankings,
                industry_averages=industry_averages,
                relative_performance=relative_performance
            )
            
        except Exception as e:
            logger.error(f"Failed to compare {symbol} to industry: {e}")
            raise FundamentalAnalysisException(
                f"Unable to perform industry comparison for {symbol}: {str(e)}",
                error_type="COMPARISON_ERROR"
            ) 
   
    # Financial Ratio Calculation Methods
    
    def calculate_pe_ratio(self, price: Decimal, eps: Decimal) -> Optional[Decimal]:
        """Calculate Price-to-Earnings ratio."""
        if not eps or eps <= 0:
            return None
        return (price / eps).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_pb_ratio(self, price: Decimal, book_value: Decimal) -> Optional[Decimal]:
        """Calculate Price-to-Book ratio."""
        if not book_value or book_value <= 0:
            return None
        return (price / book_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_roe(self, net_income: int, total_equity: int) -> Optional[Decimal]:
        """Calculate Return on Equity."""
        if not total_equity or total_equity <= 0:
            return None
        roe = Decimal(net_income) / Decimal(total_equity)
        return roe.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def calculate_debt_to_equity(self, total_debt: int, total_equity: int) -> Optional[Decimal]:
        """Calculate Debt-to-Equity ratio."""
        if not total_equity or total_equity <= 0:
            return None
        if not total_debt:
            return Decimal('0.00')
        ratio = Decimal(total_debt) / Decimal(total_equity)
        return ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_current_ratio(self, current_assets: int, current_liabilities: int) -> Optional[Decimal]:
        """Calculate Current Ratio (liquidity measure)."""
        if not current_liabilities or current_liabilities <= 0:
            return None
        if not current_assets:
            return Decimal('0.00')
        ratio = Decimal(current_assets) / Decimal(current_liabilities)
        return ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_quick_ratio(self, current_assets: int, inventory: int, current_liabilities: int) -> Optional[Decimal]:
        """Calculate Quick Ratio (acid-test ratio)."""
        if not current_liabilities or current_liabilities <= 0:
            return None
        quick_assets = (current_assets or 0) - (inventory or 0)
        if quick_assets < 0:
            quick_assets = 0
        ratio = Decimal(quick_assets) / Decimal(current_liabilities)
        return ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_roa(self, net_income: int, total_assets: int) -> Optional[Decimal]:
        """Calculate Return on Assets."""
        if not total_assets or total_assets <= 0:
            return None
        roa = Decimal(net_income) / Decimal(total_assets)
        return roa.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def calculate_gross_margin(self, gross_profit: int, revenue: int) -> Optional[Decimal]:
        """Calculate Gross Profit Margin."""
        if not revenue or revenue <= 0:
            return None
        if not gross_profit:
            return Decimal('0.00')
        margin = Decimal(gross_profit) / Decimal(revenue)
        return margin.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def calculate_operating_margin(self, operating_income: int, revenue: int) -> Optional[Decimal]:
        """Calculate Operating Profit Margin."""
        if not revenue or revenue <= 0:
            return None
        if not operating_income:
            return Decimal('0.00')
        margin = Decimal(operating_income) / Decimal(revenue)
        return margin.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    # Private helper methods
    
    async def _fetch_fundamental_data(self, symbol: str) -> FundamentalData:
        """Fetch fundamental data from yfinance."""
        loop = asyncio.get_event_loop()
        
        def _fetch_sync():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or not info.get('symbol'):
                raise ValueError(f"No fundamental data available for {symbol}")
            
            return FundamentalData.from_yfinance(info, symbol)
        
        return await loop.run_in_executor(self.executor, _fetch_sync)
    
    async def _enhance_fundamental_data(self, data: FundamentalData) -> FundamentalData:
        """Enhance fundamental data with additional calculated ratios."""
        # If we have raw financial data, calculate additional ratios
        enhanced_data = data.model_copy()
        
        # Calculate ROE if we have net income and equity
        if data.net_income and data.total_equity and not data.roe:
            enhanced_data.roe = self.calculate_roe(data.net_income, data.total_equity)
        
        # Calculate debt-to-equity if we have debt and equity
        if data.total_debt is not None and data.total_equity and not data.debt_to_equity:
            enhanced_data.debt_to_equity = self.calculate_debt_to_equity(data.total_debt, data.total_equity)
        
        return enhanced_data
    
    def _calculate_health_score(self, data: FundamentalData) -> Tuple[int, List[str], List[str], Dict[str, Any]]:
        """Calculate comprehensive company health score."""
        score = 50  # Base score
        strengths = []
        weaknesses = []
        key_metrics = {}
        
        # Profitability Analysis (25 points)
        if data.roe:
            key_metrics['roe'] = float(data.roe)
            if data.roe >= Decimal('0.20'):  # 20%+ ROE
                score += 15
                strengths.append(f"Excellent ROE of {data.roe:.1%}")
            elif data.roe >= Decimal('0.15'):  # 15-20% ROE
                score += 10
                strengths.append(f"Strong ROE of {data.roe:.1%}")
            elif data.roe >= Decimal('0.10'):  # 10-15% ROE
                score += 5
                strengths.append(f"Good ROE of {data.roe:.1%}")
            elif data.roe < Decimal('0.05'):  # <5% ROE
                score -= 10
                weaknesses.append(f"Low ROE of {data.roe:.1%}")
        
        if data.profit_margin:
            key_metrics['profit_margin'] = float(data.profit_margin)
            if data.profit_margin >= Decimal('0.20'):  # 20%+ margin
                score += 10
                strengths.append(f"High profit margin of {data.profit_margin:.1%}")
            elif data.profit_margin >= Decimal('0.10'):  # 10-20% margin
                score += 5
            elif data.profit_margin < Decimal('0.02'):  # <2% margin
                score -= 10
                weaknesses.append(f"Low profit margin of {data.profit_margin:.1%}")
        
        # Valuation Analysis (20 points)
        if data.pe_ratio:
            key_metrics['pe_ratio'] = float(data.pe_ratio)
            if Decimal('10') <= data.pe_ratio <= Decimal('25'):  # Reasonable P/E
                score += 10
                strengths.append(f"Reasonable P/E ratio of {data.pe_ratio}")
            elif data.pe_ratio > Decimal('40'):  # High P/E
                score -= 5
                weaknesses.append(f"High P/E ratio of {data.pe_ratio}")
            elif data.pe_ratio < Decimal('5'):  # Very low P/E (potential issues)
                score -= 5
                weaknesses.append(f"Very low P/E ratio of {data.pe_ratio} (potential concerns)")
        
        if data.pb_ratio:
            key_metrics['pb_ratio'] = float(data.pb_ratio)
            if data.pb_ratio <= Decimal('3'):  # Reasonable P/B
                score += 5
            elif data.pb_ratio > Decimal('10'):  # High P/B
                score -= 5
                weaknesses.append(f"High P/B ratio of {data.pb_ratio}")
        
        # Financial Stability Analysis (25 points)
        if data.debt_to_equity is not None:
            key_metrics['debt_to_equity'] = float(data.debt_to_equity)
            if data.debt_to_equity <= Decimal('0.30'):  # Low debt
                score += 15
                strengths.append(f"Low debt-to-equity ratio of {data.debt_to_equity}")
            elif data.debt_to_equity <= Decimal('0.60'):  # Moderate debt
                score += 8
                strengths.append(f"Moderate debt-to-equity ratio of {data.debt_to_equity}")
            elif data.debt_to_equity <= Decimal('1.00'):  # High debt
                score -= 5
                weaknesses.append(f"High debt-to-equity ratio of {data.debt_to_equity}")
            else:  # Very high debt
                score -= 15
                weaknesses.append(f"Very high debt-to-equity ratio of {data.debt_to_equity}")
        
        # Cash Flow Analysis (15 points)
        if data.free_cash_flow:
            key_metrics['free_cash_flow'] = data.free_cash_flow
            if data.free_cash_flow > 0:
                score += 10
                strengths.append("Positive free cash flow")
            else:
                score -= 10
                weaknesses.append("Negative free cash flow")
        
        # Growth Analysis (15 points)
        if data.revenue_growth:
            key_metrics['revenue_growth'] = float(data.revenue_growth)
            if data.revenue_growth >= Decimal('0.15'):  # 15%+ growth
                score += 10
                strengths.append(f"Strong revenue growth of {data.revenue_growth:.1%}")
            elif data.revenue_growth >= Decimal('0.05'):  # 5-15% growth
                score += 5
                strengths.append(f"Positive revenue growth of {data.revenue_growth:.1%}")
            elif data.revenue_growth < Decimal('-0.05'):  # Declining revenue
                score -= 10
                weaknesses.append(f"Declining revenue growth of {data.revenue_growth:.1%}")
        
        # Dividend Analysis (bonus points)
        if data.dividend_yield:
            key_metrics['dividend_yield'] = float(data.dividend_yield)
            if Decimal('0.02') <= data.dividend_yield <= Decimal('0.06'):  # 2-6% yield
                score += 5
                strengths.append(f"Attractive dividend yield of {data.dividend_yield:.1%}")
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return score, strengths, weaknesses, key_metrics
    
    async def _fetch_peer_fundamentals(self, symbols: List[str]) -> Dict[str, FundamentalData]:
        """Fetch fundamental data for multiple peer companies."""
        peer_data = {}
        
        # Create tasks for concurrent fetching
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._safe_fetch_fundamentals(symbol))
            tasks.append((symbol, task))
        
        # Wait for all tasks to complete
        for symbol, task in tasks:
            try:
                data = await task
                if data:
                    peer_data[symbol] = data
            except Exception as e:
                logger.warning(f"Failed to fetch fundamentals for peer {symbol}: {e}")
        
        return peer_data
    
    async def _safe_fetch_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        """Safely fetch fundamental data without raising exceptions."""
        try:
            return await self.analyze_fundamentals(symbol)
        except Exception:
            return None
    
    def _calculate_industry_averages(self, peer_data: Dict[str, FundamentalData]) -> Dict[str, float]:
        """Calculate industry average metrics."""
        metrics = {
            'pe_ratio': [],
            'pb_ratio': [],
            'roe': [],
            'debt_to_equity': [],
            'profit_margin': [],
            'revenue_growth': []
        }
        
        # Collect all valid metric values
        for data in peer_data.values():
            if data.pe_ratio:
                metrics['pe_ratio'].append(float(data.pe_ratio))
            if data.pb_ratio:
                metrics['pb_ratio'].append(float(data.pb_ratio))
            if data.roe:
                metrics['roe'].append(float(data.roe))
            if data.debt_to_equity is not None:
                metrics['debt_to_equity'].append(float(data.debt_to_equity))
            if data.profit_margin:
                metrics['profit_margin'].append(float(data.profit_margin))
            if data.revenue_growth:
                metrics['revenue_growth'].append(float(data.revenue_growth))
        
        # Calculate averages
        averages = {}
        for metric, values in metrics.items():
            if values:
                averages[metric] = sum(values) / len(values)
        
        return averages
    
    def _calculate_percentile_rankings(self, symbol: str, peer_data: Dict[str, FundamentalData]) -> Dict[str, float]:
        """Calculate percentile rankings for the target symbol."""
        if symbol not in peer_data:
            return {}
        
        target_data = peer_data[symbol]
        rankings = {}
        
        # Define metrics to rank (higher is better for most)
        metrics_higher_better = ['roe', 'profit_margin', 'revenue_growth']
        metrics_lower_better = ['pe_ratio', 'pb_ratio', 'debt_to_equity']
        
        for metric in metrics_higher_better:
            values = []
            target_value = getattr(target_data, metric)
            
            if target_value is not None:
                for data in peer_data.values():
                    peer_value = getattr(data, metric)
                    if peer_value is not None:
                        values.append(float(peer_value))
                
                if values:
                    target_float = float(target_value)
                    percentile = (sum(1 for v in values if v <= target_float) / len(values)) * 100
                    rankings[metric] = round(percentile, 1)
        
        for metric in metrics_lower_better:
            values = []
            target_value = getattr(target_data, metric)
            
            if target_value is not None:
                for data in peer_data.values():
                    peer_value = getattr(data, metric)
                    if peer_value is not None:
                        values.append(float(peer_value))
                
                if values:
                    target_float = float(target_value)
                    percentile = (sum(1 for v in values if v >= target_float) / len(values)) * 100
                    rankings[metric] = round(percentile, 1)
        
        return rankings
    
    def _determine_relative_performance(
        self, 
        symbol: str, 
        peer_data: Dict[str, FundamentalData], 
        industry_averages: Dict[str, float]
    ) -> Dict[str, str]:
        """Determine relative performance vs industry averages."""
        if symbol not in peer_data:
            return {}
        
        target_data = peer_data[symbol]
        performance = {}
        
        # Compare each metric to industry average
        for metric, avg_value in industry_averages.items():
            target_value = getattr(target_data, metric)
            
            if target_value is not None:
                target_float = float(target_value)
                
                # Define threshold for "at average" (within 10%)
                threshold = abs(avg_value * 0.1)
                
                if metric in ['roe', 'profit_margin', 'revenue_growth']:
                    # Higher is better
                    if target_float > avg_value + threshold:
                        performance[metric] = "Above Average"
                    elif target_float < avg_value - threshold:
                        performance[metric] = "Below Average"
                    else:
                        performance[metric] = "At Average"
                else:
                    # Lower is better (P/E, P/B, debt ratios)
                    if target_float < avg_value - threshold:
                        performance[metric] = "Above Average"
                    elif target_float > avg_value + threshold:
                        performance[metric] = "Below Average"
                    else:
                        performance[metric] = "At Average"
        
        return performance