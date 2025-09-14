"""
Risk Assessment API endpoints.

This module provides REST API endpoints for comprehensive risk assessment
including individual stock risk analysis, portfolio risk assessment,
correlation analysis, and scenario modeling.
"""

import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from datetime import datetime

from ..services.risk_assessment import RiskAssessmentService, RiskAssessmentException, MarketCondition
from ..services.data_aggregation import DataAggregationService
from ..models.analysis import RiskLevel
from ..core.dependencies import get_current_user
from ..models.user import User


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/risk", tags=["Risk Assessment"])

# Initialize services
risk_service = RiskAssessmentService()


class StockRiskRequest(BaseModel):
    """Request model for stock risk assessment."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    include_correlation: bool = Field(True, description="Include correlation analysis")
    include_scenarios: bool = Field(True, description="Include scenario analysis")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class PortfolioPosition(BaseModel):
    """Portfolio position model."""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    quantity: float = Field(..., gt=0, description="Number of shares")
    value: float = Field(..., gt=0, description="Position value in USD")
    sector: Optional[str] = Field(None, description="Stock sector")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class PortfolioRiskRequest(BaseModel):
    """Request model for portfolio risk assessment."""
    
    positions: List[PortfolioPosition] = Field(..., min_items=1, description="Portfolio positions")
    include_correlation_matrix: bool = Field(True, description="Include correlation matrix analysis")
    
    @validator('positions')
    def validate_positions(cls, v):
        if len(v) > 100:
            raise ValueError('Portfolio cannot exceed 100 positions')
        
        # Check for duplicate symbols
        symbols = [pos.symbol for pos in v]
        if len(symbols) != len(set(symbols)):
            raise ValueError('Duplicate symbols not allowed in portfolio')
        
        return v


class ScenarioAnalysisRequest(BaseModel):
    """Request model for scenario analysis."""
    
    symbols: List[str] = Field(..., min_items=1, max_items=20, description="Stock symbols to analyze")
    scenarios: Optional[List[MarketCondition]] = Field(None, description="Specific scenarios to analyze")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        return [symbol.upper().strip() for symbol in v]


@router.post("/stock", 
    summary="Assess individual stock risk",
    description="Perform comprehensive risk assessment for a single stock including volatility, correlation, and scenario analysis")
async def assess_stock_risk(
    request: StockRiskRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Assess comprehensive risk for an individual stock.
    
    Args:
        request: Stock risk assessment request
        current_user: Authenticated user
        
    Returns:
        Comprehensive risk assessment data
        
    Raises:
        HTTPException: If assessment fails
    """
    try:
        logger.info(f"User {current_user.id} requesting risk assessment for {request.symbol}")
        
        assessment = await risk_service.assess_stock_risk(
            symbol=request.symbol,
            include_correlation=request.include_correlation,
            include_scenarios=request.include_scenarios
        )
        
        logger.info(f"Completed risk assessment for {request.symbol}: {assessment['overall_risk_level']}")
        return assessment
        
    except RiskAssessmentException as e:
        logger.error(f"Risk assessment failed for {request.symbol}: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.error_type,
                "message": e.message,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in stock risk assessment: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during risk assessment"
        )


@router.post("/portfolio",
    summary="Assess portfolio risk",
    description="Perform comprehensive risk assessment for a portfolio including diversification, concentration, and correlation analysis")
async def assess_portfolio_risk(
    request: PortfolioRiskRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Assess comprehensive risk for a portfolio.
    
    Args:
        request: Portfolio risk assessment request
        current_user: Authenticated user
        
    Returns:
        Portfolio risk assessment data
        
    Raises:
        HTTPException: If assessment fails
    """
    try:
        logger.info(f"User {current_user.id} requesting portfolio risk assessment for {len(request.positions)} positions")
        
        # Convert positions to dict format expected by service
        positions = [
            {
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'value': pos.value,
                'sector': pos.sector
            }
            for pos in request.positions
        ]
        
        portfolio_risk = await risk_service.assess_portfolio_risk(
            positions=positions,
            include_correlation_matrix=request.include_correlation_matrix
        )
        
        # Convert to dict for JSON response
        result = {
            'total_value': float(portfolio_risk.total_value),
            'overall_risk_level': portfolio_risk.overall_risk_level.value,
            'diversification_score': portfolio_risk.diversification_score,
            'concentration_risk': portfolio_risk.concentration_risk,
            'correlation_risk': portfolio_risk.correlation_risk,
            'sector_concentration': portfolio_risk.sector_concentration,
            'risk_metrics': [metric.__dict__ for metric in portfolio_risk.risk_metrics],
            'positions': portfolio_risk.positions,
            'assessment_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Completed portfolio risk assessment: {portfolio_risk.overall_risk_level}")
        return result
        
    except RiskAssessmentException as e:
        logger.error(f"Portfolio risk assessment failed: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.error_type,
                "message": e.message,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in portfolio risk assessment: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during portfolio risk assessment"
        )


@router.post("/scenario-analysis",
    summary="Perform scenario analysis",
    description="Analyze how stocks might perform under different market conditions")
async def perform_scenario_analysis(
    request: ScenarioAnalysisRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform scenario analysis for multiple stocks.
    
    Args:
        request: Scenario analysis request
        current_user: Authenticated user
        
    Returns:
        Scenario analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"User {current_user.id} requesting scenario analysis for {len(request.symbols)} symbols")
        
        results = {}
        
        for symbol in request.symbols:
            try:
                assessment = await risk_service.assess_stock_risk(
                    symbol=symbol,
                    include_correlation=True,
                    include_scenarios=True
                )
                
                results[symbol] = {
                    'scenario_analysis': assessment.get('scenario_analysis', []),
                    'correlation_data': assessment.get('correlation_data'),
                    'overall_risk_level': assessment.get('overall_risk_level')
                }
                
            except Exception as e:
                logger.warning(f"Failed scenario analysis for {symbol}: {e}")
                results[symbol] = {
                    'error': str(e),
                    'scenario_analysis': [],
                    'correlation_data': None,
                    'overall_risk_level': 'UNKNOWN'
                }
        
        response = {
            'results': results,
            'analysis_timestamp': datetime.now().isoformat(),
            'scenarios_analyzed': [scenario.value for scenario in MarketCondition]
        }
        
        logger.info(f"Completed scenario analysis for {len(request.symbols)} symbols")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in scenario analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during scenario analysis"
        )


@router.get("/correlation/{symbol}",
    summary="Get correlation analysis",
    description="Get correlation analysis for a stock against market benchmarks")
async def get_correlation_analysis(
    symbol: str,
    benchmark: Optional[str] = Query("SPY", description="Benchmark symbol for correlation"),
    period_days: Optional[int] = Query(252, ge=30, le=1000, description="Analysis period in days"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get correlation analysis for a stock.
    
    Args:
        symbol: Stock ticker symbol
        benchmark: Benchmark symbol for correlation analysis
        period_days: Analysis period in days
        current_user: Authenticated user
        
    Returns:
        Correlation analysis data
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        symbol = symbol.upper().strip()
        benchmark = benchmark.upper().strip()
        
        logger.info(f"User {current_user.id} requesting correlation analysis for {symbol} vs {benchmark}")
        
        # Get basic risk assessment which includes correlation
        assessment = await risk_service.assess_stock_risk(
            symbol=symbol,
            include_correlation=True,
            include_scenarios=False
        )
        
        correlation_data = assessment.get('correlation_data')
        if not correlation_data:
            raise HTTPException(
                status_code=404,
                detail=f"Correlation data not available for {symbol}"
            )
        
        # Add additional correlation metrics
        result = {
            'symbol': symbol,
            'benchmark': correlation_data['benchmark'],
            'correlation': correlation_data['correlation'],
            'beta': correlation_data['beta'],
            'r_squared': correlation_data['r_squared'],
            'period_days': correlation_data['period_days'],
            'last_updated': correlation_data['last_updated'],
            'interpretation': _interpret_correlation(correlation_data['correlation'], correlation_data['beta']),
            'risk_implications': _get_correlation_risk_implications(correlation_data['correlation'], correlation_data['beta'])
        }
        
        logger.info(f"Completed correlation analysis for {symbol}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in correlation analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during correlation analysis"
        )


@router.get("/risk-factors",
    summary="Get risk factor definitions",
    description="Get definitions and explanations of various risk factors")
async def get_risk_factor_definitions() -> Dict[str, Any]:
    """
    Get definitions and explanations of risk factors.
    
    Returns:
        Risk factor definitions and explanations
    """
    return {
        'risk_levels': {
            'LOW': {
                'description': 'Low risk with stable fundamentals and low volatility',
                'characteristics': ['Low volatility', 'Strong fundamentals', 'High liquidity'],
                'suitable_for': 'Conservative investors seeking capital preservation'
            },
            'MODERATE': {
                'description': 'Moderate risk with balanced risk/reward profile',
                'characteristics': ['Moderate volatility', 'Decent fundamentals', 'Adequate liquidity'],
                'suitable_for': 'Balanced investors seeking growth with reasonable risk'
            },
            'HIGH': {
                'description': 'High risk requiring careful monitoring',
                'characteristics': ['High volatility', 'Mixed fundamentals', 'Potential liquidity issues'],
                'suitable_for': 'Aggressive investors comfortable with significant risk'
            },
            'VERY_HIGH': {
                'description': 'Very high risk suitable only for risk-tolerant investors',
                'characteristics': ['Very high volatility', 'Weak fundamentals', 'Low liquidity'],
                'suitable_for': 'Speculative investors with high risk tolerance'
            }
        },
        'risk_categories': {
            'MARKET_RISK': 'Risk from overall market movements and economic conditions',
            'LIQUIDITY_RISK': 'Risk from difficulty buying or selling the security',
            'VOLATILITY_RISK': 'Risk from price fluctuations and instability',
            'FUNDAMENTAL_RISK': 'Risk from company-specific financial health issues',
            'CONCENTRATION_RISK': 'Risk from lack of diversification',
            'CORRELATION_RISK': 'Risk from high correlation between holdings'
        },
        'market_conditions': {
            condition.value: {
                'description': _get_market_condition_description(condition),
                'typical_duration': _get_typical_duration(condition),
                'risk_characteristics': _get_condition_risk_characteristics(condition)
            }
            for condition in MarketCondition
        }
    }


def _interpret_correlation(correlation: float, beta: float) -> str:
    """Interpret correlation and beta values."""
    if correlation > 0.8:
        corr_desc = "very high positive correlation"
    elif correlation > 0.6:
        corr_desc = "high positive correlation"
    elif correlation > 0.3:
        corr_desc = "moderate positive correlation"
    elif correlation > -0.3:
        corr_desc = "low correlation"
    elif correlation > -0.6:
        corr_desc = "moderate negative correlation"
    else:
        corr_desc = "high negative correlation"
    
    if beta > 1.5:
        beta_desc = "much more volatile than market"
    elif beta > 1.2:
        beta_desc = "more volatile than market"
    elif beta > 0.8:
        beta_desc = "similar volatility to market"
    else:
        beta_desc = "less volatile than market"
    
    return f"Stock shows {corr_desc} with market and is {beta_desc} (β={beta:.2f})"


def _get_correlation_risk_implications(correlation: float, beta: float) -> List[str]:
    """Get risk implications of correlation and beta."""
    implications = []
    
    if correlation > 0.8:
        implications.append("High correlation means stock will likely move with market trends")
    if beta > 1.5:
        implications.append("High beta indicates amplified market movements - higher risk and potential reward")
    elif beta < 0.5:
        implications.append("Low beta provides some protection during market downturns")
    
    if correlation > 0.6 and beta > 1.2:
        implications.append("Stock is likely to experience significant losses during market downturns")
    
    return implications


def _get_market_condition_description(condition: MarketCondition) -> str:
    """Get description for market condition."""
    descriptions = {
        MarketCondition.BULL_MARKET: "Rising market with strong investor confidence and economic growth",
        MarketCondition.BEAR_MARKET: "Declining market with pessimistic sentiment and economic concerns",
        MarketCondition.SIDEWAYS_MARKET: "Range-bound market with mixed signals and uncertainty",
        MarketCondition.HIGH_VOLATILITY: "Unstable market with large price swings and uncertainty",
        MarketCondition.RECESSION: "Economic downturn with declining GDP and corporate earnings",
        MarketCondition.MARKET_CRASH: "Severe market decline with panic selling and systemic risk"
    }
    return descriptions.get(condition, "Market condition")


def _get_typical_duration(condition: MarketCondition) -> str:
    """Get typical duration for market condition."""
    durations = {
        MarketCondition.BULL_MARKET: "1-3 years",
        MarketCondition.BEAR_MARKET: "6-18 months",
        MarketCondition.SIDEWAYS_MARKET: "3-12 months",
        MarketCondition.HIGH_VOLATILITY: "Weeks to months",
        MarketCondition.RECESSION: "6-18 months",
        MarketCondition.MARKET_CRASH: "Days to weeks"
    }
    return durations.get(condition, "Variable")


def _get_condition_risk_characteristics(condition: MarketCondition) -> List[str]:
    """Get risk characteristics for market condition."""
    characteristics = {
        MarketCondition.BULL_MARKET: ["Low downside risk", "High opportunity cost of not investing", "Overvaluation risk"],
        MarketCondition.BEAR_MARKET: ["High downside risk", "Value opportunities", "Liquidity concerns"],
        MarketCondition.SIDEWAYS_MARKET: ["Moderate risk", "Range-trading opportunities", "Breakout risk"],
        MarketCondition.HIGH_VOLATILITY: ["Extreme price swings", "Timing risk", "Emotional decision risk"],
        MarketCondition.RECESSION: ["Fundamental deterioration", "Credit risk", "Unemployment impact"],
        MarketCondition.MARKET_CRASH: ["Severe losses", "Liquidity crisis", "Systemic risk"]
    }
    return characteristics.get(condition, ["Variable risk characteristics"])