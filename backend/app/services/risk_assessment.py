"""
Comprehensive Risk Assessment Service.

This module provides advanced risk assessment capabilities including volatility analysis,
correlation analysis, scenario modeling, and portfolio risk assessment.
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from ..models.analysis import RiskLevel
from ..models.stock import MarketData
from ..models.fundamental import FundamentalData
from ..models.technical import TechnicalData
from .data_aggregation import DataAggregationService, DataAggregationException


# Configure logging
logger = logging.getLogger(__name__)


class MarketCondition(str, Enum):
    """Market condition scenarios for risk assessment."""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS_MARKET = "sideways_market"
    HIGH_VOLATILITY = "high_volatility"
    RECESSION = "recession"
    MARKET_CRASH = "market_crash"


class RiskCategory(str, Enum):
    """Categories of risk factors."""
    MARKET_RISK = "market_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    VOLATILITY_RISK = "volatility_risk"
    FUNDAMENTAL_RISK = "fundamental_risk"
    CONCENTRATION_RISK = "concentration_risk"
    CORRELATION_RISK = "correlation_risk"


@dataclass
class RiskMetric:
    """Individual risk metric data."""
    name: str
    value: float
    risk_level: RiskLevel
    description: str
    impact: str  # High, Medium, Low
    mitigation: str


@dataclass
class CorrelationData:
    """Correlation analysis data."""
    symbol: str
    benchmark: str
    correlation: float
    beta: float
    r_squared: float
    period_days: int
    last_updated: datetime


@dataclass
class ScenarioResult:
    """Scenario analysis result."""
    scenario: MarketCondition
    expected_return: float
    worst_case_return: float
    best_case_return: float
    probability: float
    description: str


@dataclass
class PortfolioRisk:
    """Portfolio-level risk assessment."""
    total_value: Decimal
    positions: List[Dict[str, Any]]
    overall_risk_level: RiskLevel
    diversification_score: int  # 0-100
    concentration_risk: float
    correlation_risk: float
    sector_concentration: Dict[str, float]
    risk_metrics: List[RiskMetric]


class RiskAssessmentException(Exception):
    """Custom exception for risk assessment errors."""
    
    def __init__(self, message: str, error_type: str = "RISK_ASSESSMENT_ERROR", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class RiskAssessmentService:
    """
    Comprehensive Risk Assessment Service.
    
    Provides advanced risk analysis including volatility metrics, correlation analysis,
    scenario modeling, and portfolio risk assessment.
    """
    
    def __init__(self, data_service: Optional[DataAggregationService] = None):
        """Initialize the risk assessment service."""
        self.data_service = data_service or DataAggregationService()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Market benchmarks for correlation analysis
        self.benchmarks = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ 100',
            'IWM': 'Russell 2000',
            'VTI': 'Total Stock Market'
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            'volatility': {'low': 0.15, 'moderate': 0.25, 'high': 0.40, 'very_high': 0.60},
            'beta': {'low': 0.8, 'moderate': 1.2, 'high': 1.5, 'very_high': 2.0},
            'correlation': {'low': 0.3, 'moderate': 0.6, 'high': 0.8, 'very_high': 0.9},
            'debt_ratio': {'low': 0.30, 'moderate': 0.60, 'high': 1.00, 'very_high': 2.00},
            'liquidity': {'low': 1000000, 'moderate': 500000, 'high': 100000, 'very_high': 50000}
        }
        
        # Scenario probabilities (based on historical data)
        self.scenario_probabilities = {
            MarketCondition.BULL_MARKET: 0.35,
            MarketCondition.BEAR_MARKET: 0.20,
            MarketCondition.SIDEWAYS_MARKET: 0.30,
            MarketCondition.HIGH_VOLATILITY: 0.10,
            MarketCondition.RECESSION: 0.04,
            MarketCondition.MARKET_CRASH: 0.01
        }
    
    async def assess_stock_risk(
        self,
        symbol: str,
        market_data: Optional[MarketData] = None,
        fundamental_data: Optional[FundamentalData] = None,
        technical_data: Optional[TechnicalData] = None,
        include_correlation: bool = True,
        include_scenarios: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment for a single stock.
        
        Args:
            symbol: Stock ticker symbol
            market_data: Current market data (optional, will fetch if not provided)
            fundamental_data: Fundamental data (optional)
            technical_data: Technical data (optional)
            include_correlation: Whether to include correlation analysis
            include_scenarios: Whether to include scenario analysis
            
        Returns:
            Comprehensive risk assessment dictionary
        """
        symbol = symbol.upper().strip()
        
        try:
            logger.info(f"Starting comprehensive risk assessment for {symbol}")
            
            # Fetch data if not provided
            if not market_data:
                market_data = await self.data_service.get_market_data(symbol)
            
            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(
                symbol, market_data, fundamental_data, technical_data
            )
            
            # Perform correlation analysis
            correlation_data = None
            if include_correlation:
                correlation_data = await self._analyze_correlations(symbol)
            
            # Perform scenario analysis
            scenario_results = None
            if include_scenarios:
                scenario_results = await self._perform_scenario_analysis(
                    symbol, market_data, correlation_data
                )
            
            # Determine overall risk level
            overall_risk_level = self._determine_overall_risk_level(risk_metrics)
            
            # Generate risk warnings and mitigation suggestions
            warnings = self._generate_risk_warnings(risk_metrics, overall_risk_level)
            mitigations = self._generate_mitigation_suggestions(risk_metrics, overall_risk_level)
            
            # Compile comprehensive assessment
            assessment = {
                'symbol': symbol,
                'overall_risk_level': overall_risk_level,
                'risk_score': self._calculate_risk_score(risk_metrics),
                'risk_metrics': [metric.__dict__ for metric in risk_metrics],
                'correlation_data': correlation_data.__dict__ if correlation_data else None,
                'scenario_analysis': [result.__dict__ for result in scenario_results] if scenario_results else None,
                'risk_warnings': warnings,
                'mitigation_suggestions': mitigations,
                'assessment_timestamp': datetime.now(),
                'data_sources': {
                    'market_data': market_data.timestamp if market_data else None,
                    'fundamental_data': fundamental_data.last_updated if fundamental_data else None,
                    'technical_data': technical_data.timestamp if technical_data else None
                }
            }
            
            logger.info(f"Completed risk assessment for {symbol}: {overall_risk_level}")
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to assess risk for {symbol}: {e}")
            raise RiskAssessmentException(
                f"Unable to assess risk for {symbol}: {str(e)}",
                error_type="ASSESSMENT_FAILED",
                suggestions=[
                    "Check if symbol exists and is actively traded",
                    "Ensure sufficient historical data is available",
                    "Try again later if data sources are temporarily unavailable"
                ]
            )
    
    async def assess_portfolio_risk(
        self,
        positions: List[Dict[str, Any]],
        include_correlation_matrix: bool = True
    ) -> PortfolioRisk:
        """
        Assess risk for a portfolio of positions.
        
        Args:
            positions: List of position dictionaries with symbol, quantity, value
            include_correlation_matrix: Whether to calculate correlation matrix
            
        Returns:
            PortfolioRisk object with comprehensive portfolio risk analysis
        """
        try:
            logger.info(f"Assessing portfolio risk for {len(positions)} positions")
            
            if not positions:
                raise RiskAssessmentException("Portfolio cannot be empty")
            
            # Calculate total portfolio value
            total_value = sum(Decimal(str(pos.get('value', 0))) for pos in positions)
            
            # Assess individual position risks
            position_risks = []
            for position in positions:
                symbol = position.get('symbol', '').upper()
                if symbol:
                    risk_assessment = await self.assess_stock_risk(
                        symbol, include_correlation=include_correlation_matrix
                    )
                    position_risks.append({
                        'symbol': symbol,
                        'weight': float(Decimal(str(position.get('value', 0))) / total_value),
                        'risk_assessment': risk_assessment
                    })
            
            # Calculate portfolio-level metrics
            diversification_score = self._calculate_diversification_score(position_risks)
            concentration_risk = self._calculate_concentration_risk(position_risks)
            sector_concentration = self._calculate_sector_concentration(positions)
            
            # Calculate correlation risk
            correlation_risk = 0.0
            if include_correlation_matrix and len(position_risks) > 1:
                correlation_risk = await self._calculate_portfolio_correlation_risk(position_risks)
            
            # Determine overall portfolio risk level
            overall_risk_level = self._determine_portfolio_risk_level(
                position_risks, concentration_risk, correlation_risk
            )
            
            # Generate portfolio risk metrics
            portfolio_risk_metrics = self._generate_portfolio_risk_metrics(
                position_risks, concentration_risk, correlation_risk, diversification_score
            )
            
            return PortfolioRisk(
                total_value=total_value,
                positions=position_risks,
                overall_risk_level=overall_risk_level,
                diversification_score=diversification_score,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk,
                sector_concentration=sector_concentration,
                risk_metrics=portfolio_risk_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to assess portfolio risk: {e}")
            raise RiskAssessmentException(
                f"Unable to assess portfolio risk: {str(e)}",
                error_type="PORTFOLIO_ASSESSMENT_FAILED"
            )
    
    async def _calculate_risk_metrics(
        self,
        symbol: str,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData]
    ) -> List[RiskMetric]:
        """Calculate comprehensive risk metrics for a stock."""
        metrics = []
        
        try:
            # Volatility risk (using ATR if available, otherwise calculate from price data)
            volatility_risk = await self._calculate_volatility_risk(symbol, market_data, technical_data)
            if volatility_risk:
                metrics.append(volatility_risk)
            
            # Liquidity risk
            liquidity_risk = self._calculate_liquidity_risk(market_data)
            if liquidity_risk:
                metrics.append(liquidity_risk)
            
            # Fundamental risks
            if fundamental_data:
                fund_risks = self._calculate_fundamental_risks(fundamental_data)
                metrics.extend(fund_risks)
            
            # Technical risks
            if technical_data:
                tech_risks = self._calculate_technical_risks(technical_data, market_data)
                metrics.extend(tech_risks)
            
            # Market position risk (52-week position)
            position_risk = self._calculate_position_risk(market_data)
            if position_risk:
                metrics.append(position_risk)
            
        except Exception as e:
            logger.warning(f"Error calculating risk metrics for {symbol}: {e}")
        
        return metrics
    
    async def _calculate_volatility_risk(
        self,
        symbol: str,
        market_data: MarketData,
        technical_data: Optional[TechnicalData]
    ) -> Optional[RiskMetric]:
        """Calculate volatility-based risk metric."""
        try:
            # Use ATR if available from technical data
            if technical_data and technical_data.atr:
                atr_percent = float(technical_data.atr) / float(market_data.price)
                volatility = atr_percent
                source = "ATR"
            else:
                # Calculate historical volatility from price data
                volatility = await self._calculate_historical_volatility(symbol)
                source = "Historical"
                
                if volatility is None:
                    return None
            
            # Determine risk level
            if volatility >= self.risk_thresholds['volatility']['very_high']:
                risk_level = RiskLevel.VERY_HIGH
                impact = "High"
            elif volatility >= self.risk_thresholds['volatility']['high']:
                risk_level = RiskLevel.HIGH
                impact = "High"
            elif volatility >= self.risk_thresholds['volatility']['moderate']:
                risk_level = RiskLevel.MODERATE
                impact = "Medium"
            else:
                risk_level = RiskLevel.LOW
                impact = "Low"
            
            return RiskMetric(
                name="Volatility Risk",
                value=volatility,
                risk_level=risk_level,
                description=f"{source}-based volatility of {volatility:.1%} indicates {risk_level.value} price volatility risk",
                impact=impact,
                mitigation="Consider position sizing, stop-losses, or hedging strategies for high volatility stocks"
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate volatility risk for {symbol}: {e}")
            return None
    
    def _calculate_liquidity_risk(self, market_data: MarketData) -> Optional[RiskMetric]:
        """Calculate liquidity risk based on volume."""
        try:
            avg_volume = market_data.avg_volume or market_data.volume
            
            if avg_volume >= self.risk_thresholds['liquidity']['low']:
                risk_level = RiskLevel.LOW
                impact = "Low"
            elif avg_volume >= self.risk_thresholds['liquidity']['moderate']:
                risk_level = RiskLevel.MODERATE
                impact = "Medium"
            elif avg_volume >= self.risk_thresholds['liquidity']['high']:
                risk_level = RiskLevel.HIGH
                impact = "High"
            else:
                risk_level = RiskLevel.VERY_HIGH
                impact = "High"
            
            return RiskMetric(
                name="Liquidity Risk",
                value=float(avg_volume),
                risk_level=risk_level,
                description=f"Average volume of {avg_volume:,} shares indicates {risk_level.value} liquidity risk",
                impact=impact,
                mitigation="Use limit orders and avoid large position sizes in low-volume stocks"
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate liquidity risk: {e}")
            return None
    
    def _calculate_fundamental_risks(self, fundamental_data: FundamentalData) -> List[RiskMetric]:
        """Calculate fundamental-based risk metrics."""
        metrics = []
        
        try:
            # Debt risk
            if fundamental_data.debt_to_equity is not None:
                debt_ratio = float(fundamental_data.debt_to_equity)
                
                if debt_ratio >= self.risk_thresholds['debt_ratio']['very_high']:
                    risk_level = RiskLevel.VERY_HIGH
                    impact = "High"
                elif debt_ratio >= self.risk_thresholds['debt_ratio']['high']:
                    risk_level = RiskLevel.HIGH
                    impact = "High"
                elif debt_ratio >= self.risk_thresholds['debt_ratio']['moderate']:
                    risk_level = RiskLevel.MODERATE
                    impact = "Medium"
                else:
                    risk_level = RiskLevel.LOW
                    impact = "Low"
                
                metrics.append(RiskMetric(
                    name="Debt Risk",
                    value=debt_ratio,
                    risk_level=risk_level,
                    description=f"Debt-to-equity ratio of {debt_ratio:.2f} indicates {risk_level.value} financial leverage risk",
                    impact=impact,
                    mitigation="Monitor debt levels and cash flow; high debt increases financial risk during downturns"
                ))
            
            # Profitability risk
            if fundamental_data.profit_margin is not None:
                margin = float(fundamental_data.profit_margin)
                
                if margin < 0:
                    risk_level = RiskLevel.VERY_HIGH
                    impact = "High"
                elif margin < 0.02:
                    risk_level = RiskLevel.HIGH
                    impact = "High"
                elif margin < 0.05:
                    risk_level = RiskLevel.MODERATE
                    impact = "Medium"
                else:
                    risk_level = RiskLevel.LOW
                    impact = "Low"
                
                metrics.append(RiskMetric(
                    name="Profitability Risk",
                    value=margin,
                    risk_level=risk_level,
                    description=f"Profit margin of {margin:.1%} indicates {risk_level.value} profitability risk",
                    impact=impact,
                    mitigation="Monitor earnings trends and competitive position; low margins indicate operational risk"
                ))
            
            # Cash flow risk
            if fundamental_data.free_cash_flow is not None:
                fcf = fundamental_data.free_cash_flow
                
                if fcf < 0:
                    risk_level = RiskLevel.HIGH
                    impact = "High"
                    description = "Negative free cash flow indicates high financial risk"
                    mitigation = "Monitor cash burn rate and funding needs; negative FCF may require external financing"
                else:
                    risk_level = RiskLevel.LOW
                    impact = "Low"
                    description = "Positive free cash flow indicates good financial health"
                    mitigation = "Continue monitoring cash generation and capital allocation"
                
                metrics.append(RiskMetric(
                    name="Cash Flow Risk",
                    value=float(fcf),
                    risk_level=risk_level,
                    description=description,
                    impact=impact,
                    mitigation=mitigation
                ))
            
        except Exception as e:
            logger.warning(f"Failed to calculate fundamental risks: {e}")
        
        return metrics
    
    def _calculate_technical_risks(
        self, 
        technical_data: TechnicalData, 
        market_data: MarketData
    ) -> List[RiskMetric]:
        """Calculate technical-based risk metrics."""
        metrics = []
        
        try:
            # RSI extreme risk
            if technical_data.rsi is not None:
                rsi = float(technical_data.rsi)
                
                if rsi > 80 or rsi < 20:
                    risk_level = RiskLevel.HIGH
                    impact = "Medium"
                    description = f"RSI of {rsi:.1f} indicates extreme overbought/oversold conditions"
                    mitigation = "Consider waiting for RSI to normalize before entering positions"
                elif rsi > 70 or rsi < 30:
                    risk_level = RiskLevel.MODERATE
                    impact = "Medium"
                    description = f"RSI of {rsi:.1f} indicates overbought/oversold conditions"
                    mitigation = "Monitor for potential reversal signals"
                else:
                    risk_level = RiskLevel.LOW
                    impact = "Low"
                    description = f"RSI of {rsi:.1f} is in normal range"
                    mitigation = "Continue monitoring momentum indicators"
                
                metrics.append(RiskMetric(
                    name="Momentum Risk",
                    value=rsi,
                    risk_level=risk_level,
                    description=description,
                    impact=impact,
                    mitigation=mitigation
                ))
            
            # Support/resistance risk
            current_price = float(market_data.price)
            
            # Check proximity to resistance
            if technical_data.resistance_levels:
                nearest_resistance = min(
                    technical_data.resistance_levels,
                    key=lambda r: abs(r.level - market_data.price)
                )
                
                distance_to_resistance = (float(nearest_resistance.level) - current_price) / current_price
                
                if distance_to_resistance < 0.02:  # Within 2%
                    risk_level = RiskLevel.HIGH
                    impact = "Medium"
                    description = f"Price near resistance at ${nearest_resistance.level:.2f}"
                    mitigation = "Consider taking profits or waiting for breakout confirmation"
                elif distance_to_resistance < 0.05:  # Within 5%
                    risk_level = RiskLevel.MODERATE
                    impact = "Medium"
                    description = f"Price approaching resistance at ${nearest_resistance.level:.2f}"
                    mitigation = "Monitor for breakout or reversal signals"
                else:
                    risk_level = RiskLevel.LOW
                    impact = "Low"
                    description = f"Price has room to resistance at ${nearest_resistance.level:.2f}"
                    mitigation = "Continue monitoring technical levels"
                
                metrics.append(RiskMetric(
                    name="Resistance Risk",
                    value=distance_to_resistance,
                    risk_level=risk_level,
                    description=description,
                    impact=impact,
                    mitigation=mitigation
                ))
            
        except Exception as e:
            logger.warning(f"Failed to calculate technical risks: {e}")
        
        return metrics
    
    def _calculate_position_risk(self, market_data: MarketData) -> Optional[RiskMetric]:
        """Calculate risk based on 52-week position."""
        try:
            if not market_data.high_52_week or not market_data.low_52_week:
                return None
            
            current_price = float(market_data.price)
            high_52 = float(market_data.high_52_week)
            low_52 = float(market_data.low_52_week)
            
            # Calculate position within 52-week range
            position = (current_price - low_52) / (high_52 - low_52)
            
            if position > 0.9:  # Near 52-week high
                risk_level = RiskLevel.MODERATE
                impact = "Medium"
                description = f"Trading at {position:.1%} of 52-week range, near highs"
                mitigation = "Consider profit-taking or reduced position size near 52-week highs"
            elif position < 0.1:  # Near 52-week low
                risk_level = RiskLevel.HIGH
                impact = "Medium"
                description = f"Trading at {position:.1%} of 52-week range, near lows"
                mitigation = "Investigate reasons for weakness; may be opportunity or value trap"
            else:
                risk_level = RiskLevel.LOW
                impact = "Low"
                description = f"Trading at {position:.1%} of 52-week range"
                mitigation = "Monitor for trend continuation or reversal signals"
            
            return RiskMetric(
                name="52-Week Position Risk",
                value=position,
                risk_level=risk_level,
                description=description,
                impact=impact,
                mitigation=mitigation
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate position risk: {e}")
            return None
    
    async def _analyze_correlations(self, symbol: str) -> Optional[CorrelationData]:
        """Analyze correlations with market benchmarks."""
        try:
            # For now, use SPY as primary benchmark
            # In a full implementation, this would fetch historical data and calculate correlations
            benchmark = 'SPY'
            
            # Placeholder correlation calculation
            # In reality, this would fetch historical price data and calculate correlation
            correlation = 0.75  # Placeholder
            beta = 1.2  # Placeholder
            r_squared = 0.56  # Placeholder
            
            return CorrelationData(
                symbol=symbol,
                benchmark=benchmark,
                correlation=correlation,
                beta=beta,
                r_squared=r_squared,
                period_days=252,  # 1 year
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze correlations for {symbol}: {e}")
            return None
    
    async def _perform_scenario_analysis(
        self,
        symbol: str,
        market_data: MarketData,
        correlation_data: Optional[CorrelationData]
    ) -> List[ScenarioResult]:
        """Perform scenario analysis for different market conditions."""
        scenarios = []
        
        try:
            beta = correlation_data.beta if correlation_data else 1.0
            
            # Define scenario impacts based on historical data
            scenario_impacts = {
                MarketCondition.BULL_MARKET: {'market': 0.20, 'volatility': 0.15},
                MarketCondition.BEAR_MARKET: {'market': -0.25, 'volatility': 0.30},
                MarketCondition.SIDEWAYS_MARKET: {'market': 0.02, 'volatility': 0.12},
                MarketCondition.HIGH_VOLATILITY: {'market': -0.05, 'volatility': 0.40},
                MarketCondition.RECESSION: {'market': -0.35, 'volatility': 0.45},
                MarketCondition.MARKET_CRASH: {'market': -0.50, 'volatility': 0.60}
            }
            
            for condition, impact in scenario_impacts.items():
                market_return = impact['market']
                volatility = impact['volatility']
                
                # Adjust for stock's beta
                expected_return = market_return * beta
                
                # Calculate confidence intervals
                worst_case = expected_return - (2 * volatility)
                best_case = expected_return + (2 * volatility)
                
                scenarios.append(ScenarioResult(
                    scenario=condition,
                    expected_return=expected_return,
                    worst_case_return=worst_case,
                    best_case_return=best_case,
                    probability=self.scenario_probabilities[condition],
                    description=self._get_scenario_description(condition, expected_return)
                ))
            
        except Exception as e:
            logger.warning(f"Failed to perform scenario analysis for {symbol}: {e}")
        
        return scenarios
    
    def _get_scenario_description(self, condition: MarketCondition, expected_return: float) -> str:
        """Get description for scenario analysis result."""
        descriptions = {
            MarketCondition.BULL_MARKET: f"In a bull market, expect {expected_return:.1%} return with strong momentum",
            MarketCondition.BEAR_MARKET: f"In a bear market, expect {expected_return:.1%} return with significant downside",
            MarketCondition.SIDEWAYS_MARKET: f"In sideways markets, expect {expected_return:.1%} return with range-bound trading",
            MarketCondition.HIGH_VOLATILITY: f"In high volatility periods, expect {expected_return:.1%} return with large price swings",
            MarketCondition.RECESSION: f"During recession, expect {expected_return:.1%} return with fundamental deterioration",
            MarketCondition.MARKET_CRASH: f"In market crash, expect {expected_return:.1%} return with severe losses"
        }
        return descriptions.get(condition, f"Expected return: {expected_return:.1%}")
    
    async def _calculate_historical_volatility(self, symbol: str, days: int = 252) -> Optional[float]:
        """Calculate historical volatility from price data."""
        try:
            # This would fetch historical price data and calculate volatility
            # For now, return a placeholder based on typical volatility ranges
            
            # Placeholder implementation
            # In reality, this would:
            # 1. Fetch historical price data
            # 2. Calculate daily returns
            # 3. Calculate standard deviation of returns
            # 4. Annualize the volatility
            
            return 0.25  # 25% annualized volatility placeholder
            
        except Exception as e:
            logger.warning(f"Failed to calculate historical volatility for {symbol}: {e}")
            return None
    
    def _determine_overall_risk_level(self, risk_metrics: List[RiskMetric]) -> RiskLevel:
        """Determine overall risk level from individual metrics."""
        if not risk_metrics:
            return RiskLevel.MODERATE
        
        # Count risk levels
        risk_counts = {level: 0 for level in RiskLevel}
        for metric in risk_metrics:
            risk_counts[metric.risk_level] += 1
        
        # Determine overall risk based on highest risks present
        if risk_counts[RiskLevel.VERY_HIGH] > 0:
            return RiskLevel.VERY_HIGH
        elif risk_counts[RiskLevel.HIGH] >= 2:  # Multiple high risks
            return RiskLevel.VERY_HIGH
        elif risk_counts[RiskLevel.HIGH] > 0:
            return RiskLevel.HIGH
        elif risk_counts[RiskLevel.MODERATE] >= 3:  # Multiple moderate risks
            return RiskLevel.HIGH
        elif risk_counts[RiskLevel.MODERATE] > 0:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _calculate_risk_score(self, risk_metrics: List[RiskMetric]) -> int:
        """Calculate overall risk score (0-100, higher = more risky)."""
        if not risk_metrics:
            return 50
        
        risk_values = {
            RiskLevel.LOW: 20,
            RiskLevel.MODERATE: 40,
            RiskLevel.HIGH: 70,
            RiskLevel.VERY_HIGH: 90
        }
        
        total_score = sum(risk_values[metric.risk_level] for metric in risk_metrics)
        return min(100, total_score // len(risk_metrics))
    
    def _generate_risk_warnings(self, risk_metrics: List[RiskMetric], overall_risk: RiskLevel) -> List[str]:
        """Generate risk warnings based on assessment."""
        warnings = []
        
        # Overall risk warning
        if overall_risk == RiskLevel.VERY_HIGH:
            warnings.append("⚠️ VERY HIGH RISK: This investment carries significant risk of substantial losses")
        elif overall_risk == RiskLevel.HIGH:
            warnings.append("⚠️ HIGH RISK: This investment may experience significant volatility and potential losses")
        elif overall_risk == RiskLevel.MODERATE:
            warnings.append("⚠️ MODERATE RISK: This investment carries typical market risks")
        
        # Specific metric warnings
        for metric in risk_metrics:
            if metric.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                warnings.append(f"⚠️ {metric.name}: {metric.description}")
        
        return warnings
    
    def _generate_mitigation_suggestions(self, risk_metrics: List[RiskMetric], overall_risk: RiskLevel) -> List[str]:
        """Generate risk mitigation suggestions."""
        suggestions = []
        
        # Overall suggestions
        if overall_risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            suggestions.extend([
                "Consider reducing position size to limit exposure",
                "Use stop-loss orders to limit downside risk",
                "Diversify across multiple positions and sectors",
                "Monitor position closely for changes in risk profile"
            ])
        
        # Specific metric suggestions
        for metric in risk_metrics:
            if metric.mitigation and metric.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                suggestions.append(f"{metric.name}: {metric.mitigation}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    def _calculate_diversification_score(self, position_risks: List[Dict[str, Any]]) -> int:
        """Calculate portfolio diversification score (0-100)."""
        if len(position_risks) <= 1:
            return 0
        
        # Base score for number of positions
        num_positions = len(position_risks)
        base_score = min(50, num_positions * 5)  # Up to 50 points for 10+ positions
        
        # Bonus for even weight distribution
        weights = [pos['weight'] for pos in position_risks]
        max_weight = max(weights)
        
        if max_weight <= 0.1:  # No position > 10%
            base_score += 30
        elif max_weight <= 0.2:  # No position > 20%
            base_score += 20
        elif max_weight <= 0.3:  # No position > 30%
            base_score += 10
        
        # Bonus for sector diversification (would need sector data)
        # This is a placeholder - in reality would analyze sector distribution
        base_score += 20
        
        return min(100, base_score)
    
    def _calculate_concentration_risk(self, position_risks: List[Dict[str, Any]]) -> float:
        """Calculate concentration risk (0-1, higher = more concentrated)."""
        if not position_risks:
            return 0.0
        
        weights = [pos['weight'] for pos in position_risks]
        
        # Calculate Herfindahl-Hirschman Index
        hhi = sum(w ** 2 for w in weights)
        
        # Normalize to 0-1 scale
        # HHI ranges from 1/n (perfectly diversified) to 1 (fully concentrated)
        n = len(weights)
        min_hhi = 1 / n
        concentration_risk = (hhi - min_hhi) / (1 - min_hhi) if n > 1 else 1.0
        
        return concentration_risk
    
    def _calculate_sector_concentration(self, positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate sector concentration (placeholder implementation)."""
        # This would require sector data for each position
        # For now, return a placeholder
        return {"Technology": 0.4, "Healthcare": 0.3, "Finance": 0.3}
    
    async def _calculate_portfolio_correlation_risk(self, position_risks: List[Dict[str, Any]]) -> float:
        """Calculate portfolio correlation risk."""
        # This would calculate the correlation matrix between all positions
        # For now, return a placeholder based on typical correlation
        return 0.6  # Moderate correlation risk
    
    def _determine_portfolio_risk_level(
        self,
        position_risks: List[Dict[str, Any]],
        concentration_risk: float,
        correlation_risk: float
    ) -> RiskLevel:
        """Determine overall portfolio risk level."""
        # Analyze individual position risks
        high_risk_positions = sum(
            1 for pos in position_risks 
            if pos['risk_assessment']['overall_risk_level'] in ['HIGH', 'VERY_HIGH']
        )
        
        high_risk_weight = sum(
            pos['weight'] for pos in position_risks 
            if pos['risk_assessment']['overall_risk_level'] in ['HIGH', 'VERY_HIGH']
        )
        
        # Determine risk level
        if high_risk_weight > 0.5 or concentration_risk > 0.8:
            return RiskLevel.VERY_HIGH
        elif high_risk_weight > 0.3 or concentration_risk > 0.6 or correlation_risk > 0.8:
            return RiskLevel.HIGH
        elif high_risk_weight > 0.1 or concentration_risk > 0.4 or correlation_risk > 0.6:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _generate_portfolio_risk_metrics(
        self,
        position_risks: List[Dict[str, Any]],
        concentration_risk: float,
        correlation_risk: float,
        diversification_score: int
    ) -> List[RiskMetric]:
        """Generate portfolio-level risk metrics."""
        metrics = []
        
        # Concentration risk metric
        if concentration_risk > 0.8:
            risk_level = RiskLevel.VERY_HIGH
            impact = "High"
        elif concentration_risk > 0.6:
            risk_level = RiskLevel.HIGH
            impact = "High"
        elif concentration_risk > 0.4:
            risk_level = RiskLevel.MODERATE
            impact = "Medium"
        else:
            risk_level = RiskLevel.LOW
            impact = "Low"
        
        metrics.append(RiskMetric(
            name="Concentration Risk",
            value=concentration_risk,
            risk_level=risk_level,
            description=f"Portfolio concentration risk of {concentration_risk:.1%}",
            impact=impact,
            mitigation="Reduce position sizes and increase number of holdings for better diversification"
        ))
        
        # Correlation risk metric
        if correlation_risk > 0.8:
            risk_level = RiskLevel.HIGH
            impact = "High"
        elif correlation_risk > 0.6:
            risk_level = RiskLevel.MODERATE
            impact = "Medium"
        else:
            risk_level = RiskLevel.LOW
            impact = "Low"
        
        metrics.append(RiskMetric(
            name="Correlation Risk",
            value=correlation_risk,
            risk_level=risk_level,
            description=f"Portfolio correlation risk of {correlation_risk:.1%}",
            impact=impact,
            mitigation="Diversify across uncorrelated assets and sectors to reduce correlation risk"
        ))
        
        # Diversification metric
        if diversification_score < 30:
            risk_level = RiskLevel.HIGH
            impact = "High"
        elif diversification_score < 60:
            risk_level = RiskLevel.MODERATE
            impact = "Medium"
        else:
            risk_level = RiskLevel.LOW
            impact = "Low"
        
        metrics.append(RiskMetric(
            name="Diversification Risk",
            value=float(100 - diversification_score),  # Invert score for risk
            risk_level=risk_level,
            description=f"Diversification score of {diversification_score}/100",
            impact=impact,
            mitigation="Increase number of positions and ensure sector/geographic diversification"
        ))
        
        return metrics