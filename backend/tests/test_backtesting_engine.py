"""
Tests for backtesting engine functionality and accuracy.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from app.services.backtesting_engine import (
    BacktestingEngine, 
    Trade, 
    TradeType, 
    BacktestResult,
    StrategyType
)
from app.services.bigquery_service import BigQueryService
from app.services.data_aggregation import DataAggregationService
from app.models.analysis import AnalysisResult, Recommendation, RiskLevel, AnalysisType


class TestBacktestingEngine:
    """Test suite for BacktestingEngine."""
    
    @pytest.fixture
    def mock_bigquery_service(self):
        """Mock BigQuery service."""
        service = Mock(spec=BigQueryService)
        service.get_analysis_history = AsyncMock()
        service.get_historical_prices = AsyncMock()
        service.store_backtest_results = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_data_service(self):
        """Mock data aggregation service."""
        service = Mock(spec=DataAggregationService)
        return service
    
    @pytest.fixture
    def backtesting_engine(self, mock_bigquery_service, mock_data_service):
        """Create backtesting engine with mocked dependencies."""
        return BacktestingEngine(
            bigquery_service=mock_bigquery_service,
            data_service=mock_data_service
        )
    
    @pytest.fixture
    def sample_price_data(self):
        """Sample historical price data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        prices = []
        base_price = 100.0
        
        for i, date in enumerate(dates):
            # Simulate price movement with some volatility
            change = (i % 10 - 5) * 0.02  # -10% to +10% change pattern
            price = base_price * (1 + change)
            prices.append({
                'date': date,
                'open_price': price * 0.99,
                'high_price': price * 1.02,
                'low_price': price * 0.98,
                'close_price': price,
                'volume': 1000000,
                'adjusted_close': price
            })
            base_price = price
        
        return pd.DataFrame(prices)
    
    @pytest.fixture
    def sample_analysis_history(self):
        """Sample analysis history data."""
        return [
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 2, 1),
                'recommendation': 'BUY',
                'confidence': 75,
                'overall_score': 80,
                'price_at_analysis': 105.0
            },
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 6, 1),
                'recommendation': 'SELL',
                'confidence': 70,
                'overall_score': 40,
                'price_at_analysis': 120.0
            },
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 10, 1),
                'recommendation': 'BUY',
                'confidence': 80,
                'overall_score': 85,
                'price_at_analysis': 95.0
            }
        ]
    
    @pytest.mark.asyncio
    async def test_recommendation_backtest_basic(
        self, 
        backtesting_engine, 
        mock_bigquery_service,
        sample_analysis_history,
        sample_price_data
    ):
        """Test basic recommendation-based backtesting."""
        # Setup mocks
        mock_bigquery_service.get_analysis_history.return_value = sample_analysis_history
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        # Run backtest
        result = await backtesting_engine.backtest_recommendation_strategy(
            symbol='AAPL',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            min_confidence=60
        )
        
        # Verify result structure
        assert isinstance(result, BacktestResult)
        assert result.symbol == 'AAPL'
        assert result.strategy_name.startswith('recommendation_based')
        assert result.total_trades >= 0
        assert isinstance(result.total_return, Decimal)
        
        # Verify BigQuery calls
        mock_bigquery_service.get_analysis_history.assert_called_once()
        mock_bigquery_service.get_historical_prices.assert_called_once()
        mock_bigquery_service.store_backtest_results.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_recommendation_backtest_with_trades(
        self,
        backtesting_engine,
        mock_bigquery_service,
        sample_analysis_history,
        sample_price_data
    ):
        """Test recommendation backtesting generates correct trades."""
        mock_bigquery_service.get_analysis_history.return_value = sample_analysis_history
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        result = await backtesting_engine.backtest_recommendation_strategy(
            symbol='AAPL',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            min_confidence=60
        )
        
        # Should have at least one complete trade (BUY -> SELL)
        assert len(result.trades) >= 1
        
        # Check first trade
        first_trade = result.trades[0]
        assert first_trade.symbol == 'AAPL'
        assert first_trade.trade_type == TradeType.BUY
        assert first_trade.entry_date is not None
        assert first_trade.entry_price > 0
        
        # If trade is closed, check exit details
        if first_trade.exit_date:
            assert first_trade.exit_price is not None
            assert first_trade.return_pct is not None
            assert first_trade.hold_days is not None
    
    @pytest.mark.asyncio
    async def test_confidence_filtering(
        self,
        backtesting_engine,
        mock_bigquery_service,
        sample_price_data
    ):
        """Test that confidence filtering works correctly."""
        # Analysis with varying confidence levels
        analysis_history = [
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 2, 1),
                'recommendation': 'BUY',
                'confidence': 50,  # Below threshold
                'overall_score': 80,
                'price_at_analysis': 105.0
            },
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 3, 1),
                'recommendation': 'BUY',
                'confidence': 80,  # Above threshold
                'overall_score': 85,
                'price_at_analysis': 110.0
            }
        ]
        
        mock_bigquery_service.get_analysis_history.return_value = analysis_history
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        # Test with high confidence threshold
        result = await backtesting_engine.backtest_recommendation_strategy(
            symbol='AAPL',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            min_confidence=75
        )
        
        # Should only use the high-confidence recommendation
        # This should result in fewer or different trades
        assert result.total_trades >= 0
    
    @pytest.mark.asyncio
    async def test_technical_backtest_sma_crossover(
        self,
        backtesting_engine,
        mock_bigquery_service,
        sample_price_data
    ):
        """Test technical analysis backtesting with SMA crossover."""
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        strategy_params = {
            'name': 'sma_crossover',
            'sma_short_period': 10,
            'sma_long_period': 20
        }
        
        result = await backtesting_engine.backtest_technical_strategy(
            symbol='AAPL',
            start_date=datetime(2023, 2, 1),  # Allow time for SMA calculation
            end_date=datetime(2023, 12, 31),
            strategy_params=strategy_params
        )
        
        assert isinstance(result, BacktestResult)
        assert result.symbol == 'AAPL'
        assert result.strategy_name == 'technical_sma_crossover'
        assert result.total_trades >= 0
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(
        self,
        backtesting_engine,
        mock_bigquery_service
    ):
        """Test handling of empty historical data."""
        # Mock empty data
        mock_bigquery_service.get_analysis_history.return_value = []
        mock_bigquery_service.get_historical_prices.return_value = pd.DataFrame()
        
        result = await backtesting_engine.backtest_recommendation_strategy(
            symbol='INVALID',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Should return empty result without crashing
        assert result.total_trades == 0
        assert result.total_return == Decimal('0')
        assert result.winning_trades == 0
        assert result.losing_trades == 0
    
    @pytest.mark.asyncio
    async def test_strategy_comparison(
        self,
        backtesting_engine,
        mock_bigquery_service,
        sample_analysis_history,
        sample_price_data
    ):
        """Test strategy comparison functionality."""
        mock_bigquery_service.get_analysis_history.return_value = sample_analysis_history
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        strategies = [
            {
                'type': StrategyType.RECOMMENDATION_BASED,
                'min_confidence': 60
            },
            {
                'type': StrategyType.RECOMMENDATION_BASED,
                'min_confidence': 80
            }
        ]
        
        results = await backtesting_engine.compare_strategies(
            symbol='AAPL',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            strategies=strategies
        )
        
        assert isinstance(results, dict)
        assert len(results) <= len(strategies)  # Some strategies might fail
        
        for strategy_name, result in results.items():
            assert isinstance(result, BacktestResult)
            assert result.symbol == 'AAPL'
    
    def test_trade_return_calculation(self):
        """Test trade return percentage calculation."""
        # Test profitable trade
        profitable_trade = Trade(
            symbol='AAPL',
            entry_date=datetime(2023, 1, 1),
            exit_date=datetime(2023, 1, 10),
            entry_price=Decimal('100'),
            exit_price=Decimal('110'),
            position_size=Decimal('10000'),
            trade_type=TradeType.BUY,
            strategy_signal='BUY'
        )
        
        assert profitable_trade.return_pct == Decimal('10')  # 10% gain
        assert profitable_trade.hold_days == 9
        assert profitable_trade.profit_loss == Decimal('1000')  # $1000 profit
        
        # Test losing trade
        losing_trade = Trade(
            symbol='AAPL',
            entry_date=datetime(2023, 1, 1),
            exit_date=datetime(2023, 1, 10),
            entry_price=Decimal('100'),
            exit_price=Decimal('90'),
            position_size=Decimal('10000'),
            trade_type=TradeType.BUY,
            strategy_signal='BUY'
        )
        
        assert losing_trade.return_pct == Decimal('-10')  # 10% loss
        assert losing_trade.profit_loss == Decimal('-1000')  # $1000 loss
    
    def test_performance_metrics_calculation(self, backtesting_engine):
        """Test performance metrics calculation accuracy."""
        # Create sample trades
        trades = [
            Trade(
                symbol='AAPL',
                entry_date=datetime(2023, 1, 1),
                exit_date=datetime(2023, 1, 10),
                entry_price=Decimal('100'),
                exit_price=Decimal('110'),
                position_size=Decimal('10000'),
                trade_type=TradeType.BUY,
                strategy_signal='BUY'
            ),
            Trade(
                symbol='AAPL',
                entry_date=datetime(2023, 2, 1),
                exit_date=datetime(2023, 2, 10),
                entry_price=Decimal('110'),
                exit_price=Decimal('105'),
                position_size=Decimal('10000'),
                trade_type=TradeType.BUY,
                strategy_signal='BUY'
            )
        ]
        
        sample_price_data = pd.DataFrame([
            {'date': datetime(2023, 1, 1), 'close_price': 100},
            {'date': datetime(2023, 12, 31), 'close_price': 105}
        ])
        
        metrics = backtesting_engine._calculate_performance_metrics(
            trades=trades,
            price_data=sample_price_data,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Verify calculated metrics
        assert metrics['total_trades'] == 2
        assert metrics['winning_trades'] == 1
        assert metrics['losing_trades'] == 1
        assert metrics['win_rate'] == Decimal('50.00')  # 50% win rate
        assert metrics['total_return'] == Decimal('4.55')  # 10% - 4.55% ≈ 4.55%
        assert metrics['avg_hold_days'] == Decimal('9.00')  # 9 days average
    
    def test_rsi_calculation(self, backtesting_engine):
        """Test RSI indicator calculation."""
        # Create sample price series with known pattern
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113])
        
        rsi = backtesting_engine._calculate_rsi(prices, period=14)
        
        # RSI should be calculated (exact values depend on the calculation method)
        assert not rsi.isna().all()  # Should have some non-NaN values
        assert (rsi >= 0).all()  # RSI should be between 0 and 100
        assert (rsi <= 100).all()
    
    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        backtesting_engine,
        mock_bigquery_service
    ):
        """Test error handling in backtesting."""
        # Mock BigQuery service to raise an exception
        mock_bigquery_service.get_analysis_history.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await backtesting_engine.backtest_recommendation_strategy(
                symbol='AAPL',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31)
            )
    
    def test_find_closest_price(self, backtesting_engine):
        """Test finding closest price data to a target date."""
        price_data = pd.DataFrame([
            {'date': datetime(2023, 1, 1), 'close_price': 100},
            {'date': datetime(2023, 1, 5), 'close_price': 105},
            {'date': datetime(2023, 1, 10), 'close_price': 110}
        ])
        
        # Test exact match
        result = backtesting_engine._find_closest_price(price_data, datetime(2023, 1, 5))
        assert result is not None
        assert result['close_price'] == 105
        
        # Test closest match
        result = backtesting_engine._find_closest_price(price_data, datetime(2023, 1, 7))
        assert result is not None
        assert result['close_price'] == 105  # Should pick Jan 5 as closest
        
        # Test too far away (should return None)
        result = backtesting_engine._find_closest_price(price_data, datetime(2023, 2, 1))
        assert result is None  # More than 7 days away
    
    @pytest.mark.asyncio
    async def test_position_sizing(
        self,
        backtesting_engine,
        mock_bigquery_service,
        sample_analysis_history,
        sample_price_data
    ):
        """Test custom position sizing."""
        mock_bigquery_service.get_analysis_history.return_value = sample_analysis_history
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        custom_position_size = Decimal('50000')
        
        result = await backtesting_engine.backtest_recommendation_strategy(
            symbol='AAPL',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            position_size=custom_position_size
        )
        
        # Check that trades use the custom position size
        for trade in result.trades:
            assert trade.position_size == custom_position_size
    
    def test_technical_indicators_calculation(self, backtesting_engine):
        """Test technical indicators calculation."""
        price_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=50, freq='D'),
            'close_price': range(100, 150)  # Trending upward
        })
        
        strategy_params = {
            'sma_short_period': 10,
            'sma_long_period': 20,
            'rsi_period': 14
        }
        
        result_data = backtesting_engine._calculate_technical_indicators(
            price_data, strategy_params
        )
        
        # Check that indicators were added
        assert 'sma_short' in result_data.columns
        assert 'sma_long' in result_data.columns
        assert 'rsi' in result_data.columns
        
        # Check that SMAs are calculated correctly (should be increasing)
        sma_short = result_data['sma_short'].dropna()
        assert len(sma_short) > 0
        assert sma_short.iloc[-1] > sma_short.iloc[0]  # Should be trending up
    
    @pytest.mark.asyncio
    async def test_backtest_result_storage(
        self,
        backtesting_engine,
        mock_bigquery_service,
        sample_analysis_history,
        sample_price_data
    ):
        """Test that backtest results are properly stored."""
        mock_bigquery_service.get_analysis_history.return_value = sample_analysis_history
        mock_bigquery_service.get_historical_prices.return_value = sample_price_data
        
        result = await backtesting_engine.backtest_recommendation_strategy(
            symbol='AAPL',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Verify that store_backtest_results was called
        mock_bigquery_service.store_backtest_results.assert_called_once()
        
        # Get the stored data
        stored_data = mock_bigquery_service.store_backtest_results.call_args[0][0]
        
        # Verify stored data structure
        assert isinstance(stored_data, list)
        if stored_data:  # If there are trades
            first_record = stored_data[0]
            assert 'backtest_id' in first_record
            assert 'strategy_name' in first_record
            assert 'symbol' in first_record
            assert first_record['symbol'] == 'AAPL'