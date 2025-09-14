"""
Backtesting engine for evaluating trading strategies and analysis performance.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import uuid
import asyncio

from ..models.analysis import AnalysisResult, Recommendation
from .bigquery_service import BigQueryService
from .data_aggregation import DataAggregationService
from .analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Types of trades in backtesting."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StrategyType(str, Enum):
    """Types of backtesting strategies."""
    RECOMMENDATION_BASED = "recommendation_based"
    TECHNICAL_SIGNALS = "technical_signals"
    FUNDAMENTAL_SIGNALS = "fundamental_signals"
    COMBINED_SIGNALS = "combined_signals"


@dataclass
class Trade:
    """Represents a single trade in backtesting."""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: Decimal
    exit_price: Optional[Decimal]
    position_size: Decimal
    trade_type: TradeType
    strategy_signal: str
    confidence: Optional[int] = None
    
    @property
    def return_pct(self) -> Optional[Decimal]:
        """Calculate return percentage."""
        if self.exit_price is None:
            return None
        
        if self.trade_type == TradeType.BUY:
            return (self.exit_price - self.entry_price) / self.entry_price * 100
        elif self.trade_type == TradeType.SELL:
            return (self.entry_price - self.exit_price) / self.entry_price * 100
        else:
            return Decimal('0')
    
    @property
    def hold_days(self) -> Optional[int]:
        """Calculate holding period in days."""
        if self.exit_date is None:
            return None
        return (self.exit_date - self.entry_date).days
    
    @property
    def profit_loss(self) -> Optional[Decimal]:
        """Calculate absolute profit/loss."""
        if self.return_pct is None:
            return None
        return self.position_size * self.return_pct / 100


@dataclass
class BacktestResult:
    """Results of a backtesting run."""
    backtest_id: str
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    trades: List[Trade]
    
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


class BacktestingEngine:
    """Engine for backtesting trading strategies."""
    
    def __init__(
        self,
        bigquery_service: BigQueryService,
        data_service: DataAggregationService,
        analysis_engine: Optional[AnalysisEngine] = None
    ):
        """Initialize backtesting engine."""
        self.bigquery_service = bigquery_service
        self.data_service = data_service
        self.analysis_engine = analysis_engine
        
        # Default backtesting parameters
        self.default_position_size = Decimal('10000')  # $10,000 per position
        self.transaction_cost = Decimal('0.001')  # 0.1% transaction cost
        self.risk_free_rate = Decimal('0.02')  # 2% risk-free rate for Sharpe ratio
    
    async def backtest_recommendation_strategy(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        position_size: Optional[Decimal] = None,
        min_confidence: int = 60
    ) -> BacktestResult:
        """
        Backtest a strategy based on historical analysis recommendations.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for backtesting
            end_date: End date for backtesting
            position_size: Position size for each trade
            min_confidence: Minimum confidence level for trades
            
        Returns:
            BacktestResult with performance metrics
        """
        backtest_id = str(uuid.uuid4())
        strategy_name = f"recommendation_based_min_conf_{min_confidence}"
        
        if position_size is None:
            position_size = self.default_position_size
        
        logger.info(f"Starting recommendation backtest for {symbol} from {start_date} to {end_date}")
        
        try:
            # Get historical analysis results
            analysis_history = await self.bigquery_service.get_analysis_history(
                symbol=symbol,
                start_date=start_date
            )
            
            if not analysis_history:
                logger.warning(f"No historical analysis data found for {symbol}")
                return self._create_empty_backtest_result(
                    backtest_id, strategy_name, symbol, start_date, end_date
                )
            
            # Get historical price data
            price_data = await self.bigquery_service.get_historical_prices(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if price_data.empty:
                logger.warning(f"No historical price data found for {symbol}")
                return self._create_empty_backtest_result(
                    backtest_id, strategy_name, symbol, start_date, end_date
                )
            
            # Convert analysis history to DataFrame for easier processing
            analysis_df = pd.DataFrame(analysis_history)
            analysis_df['analysis_date'] = pd.to_datetime(analysis_df['analysis_date'])
            
            # Filter by confidence level
            analysis_df = analysis_df[analysis_df['confidence'] >= min_confidence]
            
            # Generate trades based on recommendations
            trades = self._generate_recommendation_trades(
                analysis_df, price_data, position_size, symbol
            )
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                trades, price_data, start_date, end_date
            )
            
            # Create backtest result
            result = BacktestResult(
                backtest_id=backtest_id,
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                trades=trades,
                created_at=datetime.now(),
                **performance_metrics
            )
            
            # Store results in BigQuery
            await self._store_backtest_result(result)
            
            logger.info(f"Completed recommendation backtest for {symbol}. Total return: {result.total_return}%")
            return result
            
        except Exception as e:
            logger.error(f"Failed to run recommendation backtest for {symbol}: {e}")
            raise
    
    async def backtest_technical_strategy(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        strategy_params: Dict[str, Any],
        position_size: Optional[Decimal] = None
    ) -> BacktestResult:
        """
        Backtest a technical analysis strategy.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for backtesting
            end_date: End date for backtesting
            strategy_params: Strategy parameters (e.g., SMA periods, RSI thresholds)
            position_size: Position size for each trade
            
        Returns:
            BacktestResult with performance metrics
        """
        backtest_id = str(uuid.uuid4())
        strategy_name = f"technical_{strategy_params.get('name', 'custom')}"
        
        if position_size is None:
            position_size = self.default_position_size
        
        logger.info(f"Starting technical backtest for {symbol} with strategy: {strategy_name}")
        
        try:
            # Get historical price data
            price_data = await self.bigquery_service.get_historical_prices(
                symbol=symbol,
                start_date=start_date - timedelta(days=100),  # Extra data for indicators
                end_date=end_date
            )
            
            if price_data.empty:
                logger.warning(f"No historical price data found for {symbol}")
                return self._create_empty_backtest_result(
                    backtest_id, strategy_name, symbol, start_date, end_date
                )
            
            # Calculate technical indicators
            price_data_with_indicators = self._calculate_technical_indicators(
                price_data, strategy_params
            )
            
            # Generate trades based on technical signals
            trades = self._generate_technical_trades(
                price_data_with_indicators, strategy_params, position_size, symbol, start_date
            )
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                trades, price_data, start_date, end_date
            )
            
            # Create backtest result
            result = BacktestResult(
                backtest_id=backtest_id,
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                trades=trades,
                created_at=datetime.now(),
                **performance_metrics
            )
            
            # Store results in BigQuery
            await self._store_backtest_result(result)
            
            logger.info(f"Completed technical backtest for {symbol}. Total return: {result.total_return}%")
            return result
            
        except Exception as e:
            logger.error(f"Failed to run technical backtest for {symbol}: {e}")
            raise
    
    async def compare_strategies(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple strategies on the same symbol and time period.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for backtesting
            end_date: End date for backtesting
            strategies: List of strategy configurations
            
        Returns:
            Dictionary mapping strategy names to BacktestResult objects
        """
        results = {}
        
        for strategy_config in strategies:
            strategy_type = strategy_config.get('type', StrategyType.RECOMMENDATION_BASED)
            
            try:
                if strategy_type == StrategyType.RECOMMENDATION_BASED:
                    result = await self.backtest_recommendation_strategy(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        min_confidence=strategy_config.get('min_confidence', 60),
                        position_size=strategy_config.get('position_size')
                    )
                elif strategy_type == StrategyType.TECHNICAL_SIGNALS:
                    result = await self.backtest_technical_strategy(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        strategy_params=strategy_config.get('params', {}),
                        position_size=strategy_config.get('position_size')
                    )
                else:
                    logger.warning(f"Unsupported strategy type: {strategy_type}")
                    continue
                
                results[result.strategy_name] = result
                
            except Exception as e:
                logger.error(f"Failed to backtest strategy {strategy_config}: {e}")
                continue
        
        return results
    
    def _generate_recommendation_trades(
        self,
        analysis_df: pd.DataFrame,
        price_data: pd.DataFrame,
        position_size: Decimal,
        symbol: str
    ) -> List[Trade]:
        """Generate trades based on historical recommendations."""
        trades = []
        current_position = None
        
        # Sort analysis by date
        analysis_df = analysis_df.sort_values('analysis_date')
        
        for _, analysis in analysis_df.iterrows():
            analysis_date = analysis['analysis_date']
            recommendation = analysis['recommendation']
            confidence = analysis['confidence']
            
            # Find the closest price data
            price_row = self._find_closest_price(price_data, analysis_date)
            if price_row is None:
                continue
            
            entry_price = Decimal(str(price_row['close_price']))
            
            # Determine trade action
            if recommendation in ['BUY', 'STRONG_BUY'] and current_position is None:
                # Open long position
                current_position = Trade(
                    symbol=symbol,
                    entry_date=analysis_date,
                    exit_date=None,
                    entry_price=entry_price,
                    exit_price=None,
                    position_size=position_size,
                    trade_type=TradeType.BUY,
                    strategy_signal=recommendation,
                    confidence=confidence
                )
                
            elif recommendation in ['SELL', 'STRONG_SELL'] and current_position is not None:
                # Close long position
                current_position.exit_date = analysis_date
                current_position.exit_price = entry_price
                trades.append(current_position)
                current_position = None
                
            elif recommendation == 'HOLD':
                # Continue holding current position
                continue
        
        # Close any remaining open position at the end
        if current_position is not None:
            last_price_row = price_data.iloc[-1]
            current_position.exit_date = pd.to_datetime(last_price_row['date'])
            current_position.exit_price = Decimal(str(last_price_row['close_price']))
            trades.append(current_position)
        
        return trades
    
    def _generate_technical_trades(
        self,
        price_data: pd.DataFrame,
        strategy_params: Dict[str, Any],
        position_size: Decimal,
        symbol: str,
        start_date: datetime
    ) -> List[Trade]:
        """Generate trades based on technical indicators."""
        trades = []
        current_position = None
        
        # Filter data to start_date
        price_data = price_data[pd.to_datetime(price_data['date']) >= start_date]
        
        for idx, row in price_data.iterrows():
            date = pd.to_datetime(row['date'])
            close_price = Decimal(str(row['close_price']))
            
            # Simple moving average crossover strategy example
            if 'sma_short' in row and 'sma_long' in row:
                sma_short = row['sma_short']
                sma_long = row['sma_long']
                
                # Buy signal: short MA crosses above long MA
                if (sma_short > sma_long and 
                    idx > 0 and 
                    price_data.iloc[idx-1]['sma_short'] <= price_data.iloc[idx-1]['sma_long'] and
                    current_position is None):
                    
                    current_position = Trade(
                        symbol=symbol,
                        entry_date=date,
                        exit_date=None,
                        entry_price=close_price,
                        exit_price=None,
                        position_size=position_size,
                        trade_type=TradeType.BUY,
                        strategy_signal="SMA_CROSSOVER_BUY"
                    )
                
                # Sell signal: short MA crosses below long MA
                elif (sma_short < sma_long and 
                      idx > 0 and 
                      price_data.iloc[idx-1]['sma_short'] >= price_data.iloc[idx-1]['sma_long'] and
                      current_position is not None):
                    
                    current_position.exit_date = date
                    current_position.exit_price = close_price
                    trades.append(current_position)
                    current_position = None
        
        # Close any remaining open position
        if current_position is not None:
            last_row = price_data.iloc[-1]
            current_position.exit_date = pd.to_datetime(last_row['date'])
            current_position.exit_price = Decimal(str(last_row['close_price']))
            trades.append(current_position)
        
        return trades
    
    def _calculate_technical_indicators(
        self, 
        price_data: pd.DataFrame, 
        strategy_params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate technical indicators for backtesting."""
        df = price_data.copy()
        
        # Simple Moving Averages
        if 'sma_short_period' in strategy_params:
            df['sma_short'] = df['close_price'].rolling(
                window=strategy_params['sma_short_period']
            ).mean()
        
        if 'sma_long_period' in strategy_params:
            df['sma_long'] = df['close_price'].rolling(
                window=strategy_params['sma_long_period']
            ).mean()
        
        # RSI
        if 'rsi_period' in strategy_params:
            df['rsi'] = self._calculate_rsi(df['close_price'], strategy_params['rsi_period'])
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _find_closest_price(self, price_data: pd.DataFrame, target_date: datetime) -> Optional[pd.Series]:
        """Find the closest price data to a target date."""
        price_data['date'] = pd.to_datetime(price_data['date'])
        price_data['date_diff'] = abs(price_data['date'] - target_date)
        
        closest_idx = price_data['date_diff'].idxmin()
        
        # Only return if within 7 days
        if price_data.loc[closest_idx, 'date_diff'] <= timedelta(days=7):
            return price_data.loc[closest_idx]
        
        return None
    
    def _calculate_performance_metrics(
        self,
        trades: List[Trade],
        price_data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not trades:
            return self._get_empty_performance_metrics()
        
        # Calculate basic metrics
        returns = [trade.return_pct for trade in trades if trade.return_pct is not None]
        
        if not returns:
            return self._get_empty_performance_metrics()
        
        returns = [float(r) for r in returns]
        
        total_return = sum(returns)
        avg_return_per_trade = total_return / len(returns) if returns else 0
        
        winning_trades = len([r for r in returns if r > 0])
        losing_trades = len([r for r in returns if r < 0])
        win_rate = (winning_trades / len(returns)) * 100 if returns else 0
        
        # Calculate annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Calculate volatility
        volatility = np.std(returns) if len(returns) > 1 else 0
        
        # Calculate Sharpe ratio
        if volatility > 0:
            excess_return = annualized_return - float(self.risk_free_rate) * 100
            sharpe_ratio = excess_return / (volatility * np.sqrt(252))  # Annualized
        else:
            sharpe_ratio = None
        
        # Calculate max drawdown
        cumulative_returns = np.cumprod([1 + r/100 for r in returns])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max * 100
        max_drawdown = abs(min(drawdowns)) if len(drawdowns) > 0 else 0
        
        # Calculate average holding days
        hold_days = [trade.hold_days for trade in trades if trade.hold_days is not None]
        avg_hold_days = sum(hold_days) / len(hold_days) if hold_days else 0
        
        return {
            'total_return': Decimal(str(round(total_return, 2))),
            'annualized_return': Decimal(str(round(annualized_return, 2))),
            'win_rate': Decimal(str(round(win_rate, 2))),
            'avg_return_per_trade': Decimal(str(round(avg_return_per_trade, 2))),
            'max_drawdown': Decimal(str(round(max_drawdown, 2))),
            'sharpe_ratio': Decimal(str(round(sharpe_ratio, 2))) if sharpe_ratio is not None else None,
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'avg_hold_days': Decimal(str(round(avg_hold_days, 2))),
            'volatility': Decimal(str(round(volatility, 2))),
            'beta': None  # Would need benchmark data to calculate
        }
    
    def _get_empty_performance_metrics(self) -> Dict[str, Any]:
        """Return empty performance metrics for failed backtests."""
        return {
            'total_return': Decimal('0'),
            'annualized_return': Decimal('0'),
            'win_rate': Decimal('0'),
            'avg_return_per_trade': Decimal('0'),
            'max_drawdown': Decimal('0'),
            'sharpe_ratio': None,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_hold_days': Decimal('0'),
            'volatility': Decimal('0'),
            'beta': None
        }
    
    def _create_empty_backtest_result(
        self,
        backtest_id: str,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Create an empty backtest result for failed backtests."""
        return BacktestResult(
            backtest_id=backtest_id,
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            trades=[],
            created_at=datetime.now(),
            **self._get_empty_performance_metrics()
        )
    
    async def _store_backtest_result(self, result: BacktestResult) -> None:
        """Store backtest result in BigQuery."""
        try:
            # Convert trades to BigQuery format
            backtest_records = []
            
            for trade in result.trades:
                record = {
                    'backtest_id': result.backtest_id,
                    'strategy_name': result.strategy_name,
                    'symbol': result.symbol,
                    'start_date': result.start_date.date(),
                    'end_date': result.end_date.date(),
                    'entry_date': trade.entry_date.date() if trade.entry_date else None,
                    'exit_date': trade.exit_date.date() if trade.exit_date else None,
                    'entry_price': float(trade.entry_price),
                    'exit_price': float(trade.exit_price) if trade.exit_price else None,
                    'position_size': float(trade.position_size),
                    'return_pct': float(trade.return_pct) if trade.return_pct else None,
                    'hold_days': trade.hold_days,
                    'trade_type': trade.trade_type.value
                }
                backtest_records.append(record)
            
            # Store in BigQuery
            await self.bigquery_service.store_backtest_results(backtest_records)
            
        except Exception as e:
            logger.error(f"Failed to store backtest result: {e}")
            # Don't raise - backtest was successful even if storage failed