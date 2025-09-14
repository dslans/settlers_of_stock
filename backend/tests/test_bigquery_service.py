"""
Tests for BigQuery service functionality and data handling.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from app.services.bigquery_service import BigQueryService
from app.models.analysis import AnalysisResult, Recommendation, RiskLevel, AnalysisType, PriceTarget
from app.core.config import get_settings


class TestBigQueryService:
    """Test suite for BigQueryService."""
    
    @pytest.fixture
    def mock_bigquery_client(self):
        """Mock BigQuery client."""
        client = Mock()
        client.dataset.return_value.table.return_value = Mock()
        client.get_dataset = Mock()
        client.get_table = Mock()
        client.create_dataset = Mock()
        client.create_table = Mock()
        client.load_table_from_dataframe = Mock()
        client.insert_rows_json = Mock(return_value=[])  # No errors
        client.query = Mock()
        return client
    
    @pytest.fixture
    def bigquery_service(self, mock_bigquery_client):
        """Create BigQuery service with mocked client."""
        with patch('app.services.bigquery_service.bigquery.Client', return_value=mock_bigquery_client):
            service = BigQueryService()
            service.client = mock_bigquery_client
            return service
    
    @pytest.fixture
    def sample_price_data(self):
        """Sample price data DataFrame."""
        return pd.DataFrame({
            'Date': pd.date_range(start='2023-01-01', periods=10, freq='D'),
            'Open': [100 + i for i in range(10)],
            'High': [102 + i for i in range(10)],
            'Low': [98 + i for i in range(10)],
            'Close': [101 + i for i in range(10)],
            'Volume': [1000000 + i * 10000 for i in range(10)],
            'Adj Close': [101 + i for i in range(10)]
        })
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result."""
        return AnalysisResult(
            symbol='AAPL',
            analysis_type=AnalysisType.COMBINED,
            recommendation=Recommendation.BUY,
            confidence=75,
            overall_score=80,
            fundamental_score=85,
            technical_score=75,
            strengths=['Strong financials', 'Good technical momentum'],
            weaknesses=['High valuation'],
            risks=['Market volatility', 'Competition'],
            opportunities=['New product launch'],
            price_targets=[
                PriceTarget(target=Decimal('165'), timeframe='3M', confidence=70, rationale='Technical analysis'),
                PriceTarget(target=Decimal('180'), timeframe='1Y', confidence=65, rationale='Fundamental growth')
            ],
            risk_level=RiskLevel.MODERATE,
            analysis_timestamp=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_initialize_dataset_and_tables(self, bigquery_service, mock_bigquery_client):
        """Test dataset and table initialization."""
        # Mock that dataset and tables don't exist
        from google.cloud.exceptions import NotFound
        mock_bigquery_client.get_dataset.side_effect = NotFound("Dataset not found")
        mock_bigquery_client.get_table.side_effect = NotFound("Table not found")
        
        await bigquery_service.initialize_dataset_and_tables()
        
        # Verify dataset creation was called
        mock_bigquery_client.create_dataset.assert_called_once()
        
        # Verify table creation was called for each table
        assert mock_bigquery_client.create_table.call_count == len(bigquery_service.table_schemas)
    
    @pytest.mark.asyncio
    async def test_store_historical_prices(self, bigquery_service, mock_bigquery_client, sample_price_data):
        """Test storing historical price data."""
        # Mock successful job
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_bigquery_client.load_table_from_dataframe.return_value = mock_job
        
        await bigquery_service.store_historical_prices('AAPL', sample_price_data)
        
        # Verify BigQuery load was called
        mock_bigquery_client.load_table_from_dataframe.assert_called_once()
        
        # Get the DataFrame that was passed
        call_args = mock_bigquery_client.load_table_from_dataframe.call_args
        stored_df = call_args[0][0]  # First argument is the DataFrame
        
        # Verify data transformation
        assert 'symbol' in stored_df.columns
        assert 'created_at' in stored_df.columns
        assert stored_df['symbol'].iloc[0] == 'AAPL'
        assert 'date' in stored_df.columns
        assert 'close_price' in stored_df.columns
    
    @pytest.mark.asyncio
    async def test_store_analysis_result(self, bigquery_service, mock_bigquery_client, sample_analysis_result):
        """Test storing analysis results."""
        current_price = Decimal('150.00')
        
        await bigquery_service.store_analysis_result(sample_analysis_result, current_price)
        
        # Verify insert was called
        mock_bigquery_client.insert_rows_json.assert_called_once()
        
        # Get the inserted data
        call_args = mock_bigquery_client.insert_rows_json.call_args
        inserted_data = call_args[0][1]  # Second argument is the data list
        
        # Verify data structure
        assert len(inserted_data) == 1
        record = inserted_data[0]
        assert record['symbol'] == 'AAPL'
        assert record['recommendation'] == 'BUY'
        assert record['confidence'] == 75
        assert record['price_at_analysis'] == 150.0
        assert record['target_price_3m'] == 165.0
        assert record['target_price_1y'] == 180.0
        assert 'Strong financials' in record['strengths']
    
    @pytest.mark.asyncio
    async def test_get_historical_prices(self, bigquery_service, mock_bigquery_client):
        """Test retrieving historical price data."""
        # Mock query result
        mock_result = Mock()
        mock_result.to_dataframe.return_value = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=5, freq='D'),
            'open_price': [100, 101, 102, 103, 104],
            'high_price': [102, 103, 104, 105, 106],
            'low_price': [98, 99, 100, 101, 102],
            'close_price': [101, 102, 103, 104, 105],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000],
            'adjusted_close': [101, 102, 103, 104, 105]
        })
        mock_bigquery_client.query.return_value = mock_result
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 5)
        
        result = await bigquery_service.get_historical_prices('AAPL', start_date, end_date)
        
        # Verify query was called
        mock_bigquery_client.query.assert_called_once()
        
        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert 'close_price' in result.columns
        assert result['close_price'].iloc[0] == 101
    
    @pytest.mark.asyncio
    async def test_get_analysis_history(self, bigquery_service, mock_bigquery_client):
        """Test retrieving analysis history."""
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 1, 1),
                'recommendation': 'BUY',
                'confidence': 75,
                'overall_score': 80,
                'price_at_analysis': 150.0
            },
            {
                'symbol': 'AAPL',
                'analysis_date': datetime(2023, 2, 1),
                'recommendation': 'HOLD',
                'confidence': 60,
                'overall_score': 70,
                'price_at_analysis': 155.0
            }
        ]))
        mock_bigquery_client.query.return_value = mock_result
        
        result = await bigquery_service.get_analysis_history('AAPL', limit=10)
        
        # Verify query was called
        mock_bigquery_client.query.assert_called_once()
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['symbol'] == 'AAPL'
        assert result[0]['recommendation'] == 'BUY'
    
    @pytest.mark.asyncio
    async def test_store_backtest_results(self, bigquery_service, mock_bigquery_client):
        """Test storing backtest results."""
        backtest_results = [
            {
                'backtest_id': 'test-123',
                'strategy_name': 'test_strategy',
                'symbol': 'AAPL',
                'start_date': datetime(2023, 1, 1).date(),
                'end_date': datetime(2023, 12, 31).date(),
                'entry_date': datetime(2023, 2, 1).date(),
                'exit_date': datetime(2023, 3, 1).date(),
                'entry_price': 150.0,
                'exit_price': 160.0,
                'position_size': 10000.0,
                'return_pct': 6.67,
                'hold_days': 28,
                'trade_type': 'BUY'
            }
        ]
        
        await bigquery_service.store_backtest_results(backtest_results)
        
        # Verify insert was called
        mock_bigquery_client.insert_rows_json.assert_called_once()
        
        # Get the inserted data
        call_args = mock_bigquery_client.insert_rows_json.call_args
        inserted_data = call_args[0][1]
        
        # Verify data structure
        assert len(inserted_data) == 1
        record = inserted_data[0]
        assert record['backtest_id'] == 'test-123'
        assert record['symbol'] == 'AAPL'
        assert record['return_pct'] == 6.67
        assert 'created_at' in record
    
    @pytest.mark.asyncio
    async def test_get_backtest_results_with_filters(self, bigquery_service, mock_bigquery_client):
        """Test retrieving backtest results with filters."""
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            {
                'backtest_id': 'test-123',
                'strategy_name': 'test_strategy',
                'symbol': 'AAPL',
                'start_date': datetime(2023, 1, 1).date(),
                'end_date': datetime(2023, 12, 31).date(),
                'return_pct': 10.5,
                'created_at': datetime(2023, 1, 15)
            }
        ]))
        mock_bigquery_client.query.return_value = mock_result
        
        result = await bigquery_service.get_backtest_results(
            strategy_name='test_strategy',
            symbol='AAPL'
        )
        
        # Verify query was called
        mock_bigquery_client.query.assert_called_once()
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['strategy_name'] == 'test_strategy'
        assert result[0]['symbol'] == 'AAPL'
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, bigquery_service, mock_bigquery_client):
        """Test cleaning up old data."""
        # Mock successful job
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_bigquery_client.query.return_value = mock_job
        
        await bigquery_service.cleanup_old_data(days_to_keep=30)
        
        # Verify delete query was called
        mock_bigquery_client.query.assert_called_once()
        
        # Verify the query contains DELETE statement
        call_args = mock_bigquery_client.query.call_args
        query = call_args[0][0]  # First argument is the query string
        assert 'DELETE' in query.upper()
        assert 'backtest_results' in query
    
    @pytest.mark.asyncio
    async def test_error_handling_insert_failure(self, bigquery_service, mock_bigquery_client, sample_analysis_result):
        """Test error handling when insert fails."""
        # Mock insert failure
        mock_bigquery_client.insert_rows_json.return_value = [{'error': 'Insert failed'}]
        
        with pytest.raises(Exception) as exc_info:
            await bigquery_service.store_analysis_result(sample_analysis_result, Decimal('150'))
        
        assert 'BigQuery insert errors' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self, bigquery_service, mock_bigquery_client):
        """Test handling of empty data sets."""
        # Mock empty query result
        mock_result = Mock()
        mock_result.to_dataframe.return_value = pd.DataFrame()
        mock_bigquery_client.query.return_value = mock_result
        
        result = await bigquery_service.get_historical_prices(
            'INVALID', 
            datetime(2023, 1, 1), 
            datetime(2023, 1, 31)
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_store_empty_backtest_results(self, bigquery_service, mock_bigquery_client):
        """Test storing empty backtest results."""
        await bigquery_service.store_backtest_results([])
        
        # Should not call insert for empty data
        mock_bigquery_client.insert_rows_json.assert_not_called()
    
    def test_table_schemas_structure(self, bigquery_service):
        """Test that table schemas are properly defined."""
        schemas = bigquery_service.table_schemas
        
        # Verify all expected tables are defined
        expected_tables = ['historical_prices', 'analysis_history', 'backtest_results']
        for table in expected_tables:
            assert table in schemas
            assert len(schemas[table]) > 0  # Should have fields
        
        # Verify historical_prices schema
        price_schema = schemas['historical_prices']
        field_names = [field.name for field in price_schema]
        assert 'symbol' in field_names
        assert 'date' in field_names
        assert 'close_price' in field_names
        assert 'volume' in field_names
        
        # Verify analysis_history schema
        analysis_schema = schemas['analysis_history']
        field_names = [field.name for field in analysis_schema]
        assert 'symbol' in field_names
        assert 'recommendation' in field_names
        assert 'confidence' in field_names
        
        # Verify backtest_results schema
        backtest_schema = schemas['backtest_results']
        field_names = [field.name for field in backtest_schema]
        assert 'backtest_id' in field_names
        assert 'strategy_name' in field_names
        assert 'return_pct' in field_names
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, bigquery_service, mock_bigquery_client):
        """Test concurrent BigQuery operations."""
        # Mock successful operations
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_bigquery_client.query.return_value = mock_result
        
        # Run multiple operations concurrently
        tasks = [
            bigquery_service.get_analysis_history('AAPL'),
            bigquery_service.get_analysis_history('GOOGL'),
            bigquery_service.get_analysis_history('MSFT')
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed
        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)
        
        # Verify multiple queries were made
        assert mock_bigquery_client.query.call_count == 3
    
    @pytest.mark.asyncio
    async def test_data_type_conversion(self, bigquery_service, mock_bigquery_client, sample_price_data):
        """Test proper data type conversion for BigQuery."""
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_bigquery_client.load_table_from_dataframe.return_value = mock_job
        
        await bigquery_service.store_historical_prices('AAPL', sample_price_data)
        
        # Get the stored DataFrame
        call_args = mock_bigquery_client.load_table_from_dataframe.call_args
        stored_df = call_args[0][0]
        
        # Verify date column is properly converted
        assert stored_df['date'].dtype.name == 'object'  # Should be date objects
        
        # Verify numeric columns are present
        numeric_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        for col in numeric_columns:
            assert col in stored_df.columns
    
    @pytest.mark.asyncio
    async def test_query_parameter_handling(self, bigquery_service, mock_bigquery_client):
        """Test proper handling of query parameters."""
        mock_result = Mock()
        mock_result.to_dataframe.return_value = pd.DataFrame()
        mock_bigquery_client.query.return_value = mock_result
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        await bigquery_service.get_historical_prices('AAPL', start_date, end_date)
        
        # Verify query was called with job config
        call_args = mock_bigquery_client.query.call_args
        assert len(call_args[0]) >= 1  # Query string
        assert 'job_config' in call_args[1]  # Job config in kwargs
        
        job_config = call_args[1]['job_config']
        assert hasattr(job_config, 'query_parameters')
        assert len(job_config.query_parameters) >= 3  # symbol, start_date, end_date