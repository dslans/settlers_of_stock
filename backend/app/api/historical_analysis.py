"""
Historical analysis and backtesting API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from ..core.dependencies import get_current_user
from ..models.user import User
from ..services.bigquery_service import BigQueryService
from ..services.backtesting_engine import BacktestingEngine, StrategyType
from ..services.data_aggregation import DataAggregationService
from ..services.analysis_engine import AnalysisEngine
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
bigquery_service = BigQueryService()
data_service = DataAggregationService()
analysis_engine = AnalysisEngine()
backtesting_engine = BacktestingEngine(bigquery_service, data_service, analysis_engine)


# Request/Response Models
class BacktestRequest(BaseModel):
    """Request model for backtesting."""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    start_date: datetime = Field(..., description="Start date for backtesting")
    end_date: datetime = Field(..., description="End date for backtesting")
    strategy_type: StrategyType = Field(default=StrategyType.RECOMMENDATION_BASED, description="Type of strategy to backtest")
    min_confidence: Optional[int] = Field(default=60, ge=0, le=100, description="Minimum confidence for recommendation strategy")
    position_size: Optional[Decimal] = Field(default=None, gt=0, description="Position size for trades")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="Additional strategy parameters")


class BacktestResponse(BaseModel):
    """Response model for backtesting results."""
    backtest_id: str
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    
    # Performance metrics
    total_return: Decimal
    annualized_return: Decimal
    win_rate: Decimal
    avg_return_per_trade: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Optional[Decimal]
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_hold_days: Decimal
    
    # Risk metrics
    volatility: Decimal
    beta: Optional[Decimal]
    
    created_at: datetime


class TradeDetail(BaseModel):
    """Individual trade details."""
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: Decimal
    exit_price: Optional[Decimal]
    return_pct: Optional[Decimal]
    hold_days: Optional[int]
    trade_type: str
    strategy_signal: str
    confidence: Optional[int]


class DetailedBacktestResponse(BacktestResponse):
    """Detailed backtest response with individual trades."""
    trades: List[TradeDetail]


class AnalysisHistoryResponse(BaseModel):
    """Historical analysis response."""
    symbol: str
    analysis_date: datetime
    recommendation: str
    confidence: int
    overall_score: int
    fundamental_score: Optional[int]
    technical_score: Optional[int]
    price_at_analysis: Decimal
    target_price_3m: Optional[Decimal]
    target_price_1y: Optional[Decimal]
    risk_level: str
    strengths: List[str]
    weaknesses: List[str]
    risks: List[str]


class StrategyComparisonRequest(BaseModel):
    """Request for comparing multiple strategies."""
    symbol: str = Field(..., min_length=1, max_length=10)
    start_date: datetime
    end_date: datetime
    strategies: List[Dict[str, Any]] = Field(..., min_items=1, max_items=5)


class StrategyComparisonResponse(BaseModel):
    """Response for strategy comparison."""
    symbol: str
    start_date: datetime
    end_date: datetime
    strategies: Dict[str, BacktestResponse]
    best_strategy: str
    comparison_metrics: Dict[str, Any]


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Run a backtest for a specific strategy and symbol.
    """
    try:
        logger.info(f"Running backtest for {request.symbol} with strategy {request.strategy_type}")
        
        # Validate date range
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if request.end_date > datetime.now():
            raise HTTPException(status_code=400, detail="End date cannot be in the future")
        
        # Ensure we have enough historical data (at least 30 days)
        if (request.end_date - request.start_date).days < 30:
            raise HTTPException(status_code=400, detail="Date range must be at least 30 days")
        
        # Initialize BigQuery tables if needed
        await bigquery_service.initialize_dataset_and_tables()
        
        # Run backtest based on strategy type
        if request.strategy_type == StrategyType.RECOMMENDATION_BASED:
            result = await backtesting_engine.backtest_recommendation_strategy(
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                position_size=request.position_size,
                min_confidence=request.min_confidence or 60
            )
        elif request.strategy_type == StrategyType.TECHNICAL_SIGNALS:
            if not request.strategy_params:
                # Default technical strategy parameters
                request.strategy_params = {
                    'name': 'sma_crossover',
                    'sma_short_period': 20,
                    'sma_long_period': 50
                }
            
            result = await backtesting_engine.backtest_technical_strategy(
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                strategy_params=request.strategy_params,
                position_size=request.position_size
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported strategy type: {request.strategy_type}")
        
        # Convert to response model
        response = BacktestResponse(
            backtest_id=result.backtest_id,
            strategy_name=result.strategy_name,
            symbol=result.symbol,
            start_date=result.start_date,
            end_date=result.end_date,
            total_return=result.total_return,
            annualized_return=result.annualized_return,
            win_rate=result.win_rate,
            avg_return_per_trade=result.avg_return_per_trade,
            max_drawdown=result.max_drawdown,
            sharpe_ratio=result.sharpe_ratio,
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            avg_hold_days=result.avg_hold_days,
            volatility=result.volatility,
            beta=result.beta,
            created_at=result.created_at
        )
        
        logger.info(f"Backtest completed for {request.symbol}. Total return: {result.total_return}%")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run backtest: {str(e)}")


@router.get("/backtest/{backtest_id}", response_model=DetailedBacktestResponse)
async def get_backtest_details(
    backtest_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed backtest results including individual trades.
    """
    try:
        # Get backtest results from BigQuery
        results = await bigquery_service.get_backtest_results()
        
        # Find the specific backtest
        backtest_data = None
        for result in results:
            if result.get('backtest_id') == backtest_id:
                if backtest_data is None:
                    backtest_data = result
                    backtest_data['trades'] = []
                
                # Add trade details
                if result.get('entry_date'):
                    trade = TradeDetail(
                        entry_date=result['entry_date'],
                        exit_date=result.get('exit_date'),
                        entry_price=Decimal(str(result['entry_price'])),
                        exit_price=Decimal(str(result['exit_price'])) if result.get('exit_price') else None,
                        return_pct=Decimal(str(result['return_pct'])) if result.get('return_pct') else None,
                        hold_days=result.get('hold_days'),
                        trade_type=result['trade_type'],
                        strategy_signal=result.get('strategy_signal', ''),
                        confidence=result.get('confidence')
                    )
                    backtest_data['trades'].append(trade)
        
        if not backtest_data:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        # Calculate summary metrics from trades
        trades = backtest_data['trades']
        if trades:
            returns = [float(trade.return_pct) for trade in trades if trade.return_pct is not None]
            total_return = sum(returns)
            winning_trades = len([r for r in returns if r > 0])
            losing_trades = len([r for r in returns if r < 0])
            win_rate = (winning_trades / len(returns)) * 100 if returns else 0
            avg_return = sum(returns) / len(returns) if returns else 0
            hold_days = [trade.hold_days for trade in trades if trade.hold_days is not None]
            avg_hold_days = sum(hold_days) / len(hold_days) if hold_days else 0
        else:
            total_return = 0
            winning_trades = 0
            losing_trades = 0
            win_rate = 0
            avg_return = 0
            avg_hold_days = 0
        
        response = DetailedBacktestResponse(
            backtest_id=backtest_data['backtest_id'],
            strategy_name=backtest_data['strategy_name'],
            symbol=backtest_data['symbol'],
            start_date=backtest_data['start_date'],
            end_date=backtest_data['end_date'],
            total_return=Decimal(str(total_return)),
            annualized_return=Decimal('0'),  # Would need to calculate
            win_rate=Decimal(str(win_rate)),
            avg_return_per_trade=Decimal(str(avg_return)),
            max_drawdown=Decimal('0'),  # Would need to calculate
            sharpe_ratio=None,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_hold_days=Decimal(str(avg_hold_days)),
            volatility=Decimal('0'),  # Would need to calculate
            beta=None,
            created_at=backtest_data['created_at'],
            trades=trades
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backtest details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backtest details: {str(e)}")


@router.post("/compare-strategies", response_model=StrategyComparisonResponse)
async def compare_strategies(
    request: StrategyComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Compare multiple trading strategies on the same symbol and time period.
    """
    try:
        logger.info(f"Comparing {len(request.strategies)} strategies for {request.symbol}")
        
        # Validate date range
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # Initialize BigQuery tables if needed
        await bigquery_service.initialize_dataset_and_tables()
        
        # Run comparison
        results = await backtesting_engine.compare_strategies(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            strategies=request.strategies
        )
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid strategies could be backtested")
        
        # Convert results to response format
        strategy_responses = {}
        best_return = float('-inf')
        best_strategy = ""
        
        for strategy_name, result in results.items():
            strategy_response = BacktestResponse(
                backtest_id=result.backtest_id,
                strategy_name=result.strategy_name,
                symbol=result.symbol,
                start_date=result.start_date,
                end_date=result.end_date,
                total_return=result.total_return,
                annualized_return=result.annualized_return,
                win_rate=result.win_rate,
                avg_return_per_trade=result.avg_return_per_trade,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                total_trades=result.total_trades,
                winning_trades=result.winning_trades,
                losing_trades=result.losing_trades,
                avg_hold_days=result.avg_hold_days,
                volatility=result.volatility,
                beta=result.beta,
                created_at=result.created_at
            )
            
            strategy_responses[strategy_name] = strategy_response
            
            # Track best performing strategy
            if float(result.total_return) > best_return:
                best_return = float(result.total_return)
                best_strategy = strategy_name
        
        # Calculate comparison metrics
        returns = [float(result.total_return) for result in results.values()]
        win_rates = [float(result.win_rate) for result in results.values()]
        sharpe_ratios = [float(result.sharpe_ratio) for result in results.values() if result.sharpe_ratio is not None]
        
        comparison_metrics = {
            'avg_return': sum(returns) / len(returns) if returns else 0,
            'best_return': max(returns) if returns else 0,
            'worst_return': min(returns) if returns else 0,
            'avg_win_rate': sum(win_rates) / len(win_rates) if win_rates else 0,
            'avg_sharpe_ratio': sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else None,
            'strategy_count': len(results)
        }
        
        response = StrategyComparisonResponse(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            strategies=strategy_responses,
            best_strategy=best_strategy,
            comparison_metrics=comparison_metrics
        )
        
        logger.info(f"Strategy comparison completed. Best strategy: {best_strategy} with {best_return}% return")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare strategies: {str(e)}")


@router.get("/analysis-history/{symbol}", response_model=List[AnalysisHistoryResponse])
async def get_analysis_history(
    symbol: str,
    start_date: Optional[datetime] = Query(None, description="Start date for analysis history"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical analysis results for a symbol.
    """
    try:
        symbol = symbol.upper()
        logger.info(f"Getting analysis history for {symbol}")
        
        # Get analysis history from BigQuery
        history = await bigquery_service.get_analysis_history(
            symbol=symbol,
            start_date=start_date,
            limit=limit
        )
        
        if not history:
            return []
        
        # Convert to response format
        responses = []
        for record in history:
            response = AnalysisHistoryResponse(
                symbol=record['symbol'],
                analysis_date=record['analysis_date'],
                recommendation=record['recommendation'],
                confidence=record['confidence'],
                overall_score=record['overall_score'],
                fundamental_score=record.get('fundamental_score'),
                technical_score=record.get('technical_score'),
                price_at_analysis=Decimal(str(record['price_at_analysis'])),
                target_price_3m=Decimal(str(record['target_price_3m'])) if record.get('target_price_3m') else None,
                target_price_1y=Decimal(str(record['target_price_1y'])) if record.get('target_price_1y') else None,
                risk_level=record['risk_level'],
                strengths=record.get('strengths', []),
                weaknesses=record.get('weaknesses', []),
                risks=record.get('risks', [])
            )
            responses.append(response)
        
        logger.info(f"Retrieved {len(responses)} analysis history records for {symbol}")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to get analysis history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis history: {str(e)}")


@router.get("/backtest-history")
async def get_backtest_history(
    strategy_name: Optional[str] = Query(None, description="Filter by strategy name"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical backtest results with optional filters.
    """
    try:
        logger.info("Getting backtest history")
        
        # Get backtest results from BigQuery
        results = await bigquery_service.get_backtest_results(
            strategy_name=strategy_name,
            symbol=symbol.upper() if symbol else None,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group results by backtest_id to get summary information
        backtest_summaries = {}
        
        for result in results:
            backtest_id = result['backtest_id']
            
            if backtest_id not in backtest_summaries:
                backtest_summaries[backtest_id] = {
                    'backtest_id': backtest_id,
                    'strategy_name': result['strategy_name'],
                    'symbol': result['symbol'],
                    'start_date': result['start_date'],
                    'end_date': result['end_date'],
                    'created_at': result['created_at'],
                    'trade_count': 0,
                    'total_return': 0
                }
            
            # Aggregate trade information
            if result.get('return_pct') is not None:
                backtest_summaries[backtest_id]['trade_count'] += 1
                backtest_summaries[backtest_id]['total_return'] += float(result['return_pct'])
        
        # Convert to list and sort by creation date
        summary_list = list(backtest_summaries.values())
        summary_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        logger.info(f"Retrieved {len(summary_list)} backtest summaries")
        return summary_list
        
    except Exception as e:
        logger.error(f"Failed to get backtest history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backtest history: {str(e)}")


@router.delete("/cleanup-old-data")
async def cleanup_old_data(
    days_to_keep: int = Query(365, ge=30, le=1095, description="Number of days of data to keep"),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old backtest data to manage storage costs.
    Only removes backtest results, keeps analysis history and price data.
    """
    try:
        logger.info(f"Cleaning up data older than {days_to_keep} days")
        
        await bigquery_service.cleanup_old_data(days_to_keep)
        
        return {
            "message": f"Successfully cleaned up data older than {days_to_keep} days",
            "days_kept": days_to_keep
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old data: {str(e)}")