"""
BigQuery service for historical data storage and analysis.
Handles storing market data, analysis results, and backtesting data.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..core.config import get_settings
from ..models.stock import MarketData, Stock
from ..models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


class BigQueryService:
    """Service for BigQuery operations and historical data management."""
    
    def __init__(self):
        """Initialize BigQuery service."""
        self.settings = get_settings()
        self.client = bigquery.Client(project=self.settings.GCP_PROJECT_ID)
        self.dataset_id = "settlers_of_stock"
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Table schemas
        self.table_schemas = {
            'historical_prices': [
                bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("open_price", "NUMERIC"),
                bigquery.SchemaField("high_price", "NUMERIC"),
                bigquery.SchemaField("low_price", "NUMERIC"),
                bigquery.SchemaField("close_price", "NUMERIC", mode="REQUIRED"),
                bigquery.SchemaField("volume", "INTEGER"),
                bigquery.SchemaField("adjusted_close", "NUMERIC"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ],
            'analysis_history': [
                bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("analysis_date", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("recommendation", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("confidence", "INTEGER"),
                bigquery.SchemaField("overall_score", "INTEGER"),
                bigquery.SchemaField("fundamental_score", "INTEGER"),
                bigquery.SchemaField("technical_score", "INTEGER"),
                bigquery.SchemaField("price_at_analysis", "NUMERIC"),
                bigquery.SchemaField("target_price_3m", "NUMERIC"),
                bigquery.SchemaField("target_price_1y", "NUMERIC"),
                bigquery.SchemaField("risk_level", "STRING"),
                bigquery.SchemaField("strengths", "STRING", mode="REPEATED"),
                bigquery.SchemaField("weaknesses", "STRING", mode="REPEATED"),
                bigquery.SchemaField("risks", "STRING", mode="REPEATED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ],
            'backtest_results': [
                bigquery.SchemaField("backtest_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("strategy_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("start_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("end_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("entry_date", "DATE"),
                bigquery.SchemaField("exit_date", "DATE"),
                bigquery.SchemaField("entry_price", "NUMERIC"),
                bigquery.SchemaField("exit_price", "NUMERIC"),
                bigquery.SchemaField("position_size", "NUMERIC"),
                bigquery.SchemaField("return_pct", "NUMERIC"),
                bigquery.SchemaField("hold_days", "INTEGER"),
                bigquery.SchemaField("trade_type", "STRING"),  # BUY, SELL, HOLD
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ]
        }
    
    async def initialize_dataset_and_tables(self) -> None:
        """Initialize BigQuery dataset and tables if they don't exist."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._initialize_sync)
    
    def _initialize_sync(self) -> None:
        """Synchronous initialization of dataset and tables."""
        try:
            # Create dataset if it doesn't exist
            dataset_ref = self.client.dataset(self.dataset_id)
            try:
                self.client.get_dataset(dataset_ref)
                logger.info(f"Dataset {self.dataset_id} already exists")
            except NotFound:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = self.settings.GCP_REGION
                dataset.description = "Historical stock data and analysis results for Settlers of Stock"
                self.client.create_dataset(dataset)
                logger.info(f"Created dataset {self.dataset_id}")
            
            # Create tables if they don't exist
            for table_name, schema in self.table_schemas.items():
                table_ref = dataset_ref.table(table_name)
                try:
                    self.client.get_table(table_ref)
                    logger.info(f"Table {table_name} already exists")
                except NotFound:
                    table = bigquery.Table(table_ref, schema=schema)
                    
                    # Set partitioning for better performance
                    if table_name == 'historical_prices':
                        table.time_partitioning = bigquery.TimePartitioning(
                            type_=bigquery.TimePartitioningType.DAY,
                            field="date"
                        )
                    elif table_name in ['analysis_history', 'backtest_results']:
                        table.time_partitioning = bigquery.TimePartitioning(
                            type_=bigquery.TimePartitioningType.DAY,
                            field="created_at"
                        )
                    
                    self.client.create_table(table)
                    logger.info(f"Created table {table_name}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery dataset/tables: {e}")
            raise
    
    async def store_historical_prices(self, symbol: str, price_data: pd.DataFrame) -> None:
        """
        Store historical price data in BigQuery.
        
        Args:
            symbol: Stock ticker symbol
            price_data: DataFrame with columns: Date, Open, High, Low, Close, Volume, Adj Close
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor, 
            self._store_historical_prices_sync, 
            symbol, 
            price_data
        )
    
    def _store_historical_prices_sync(self, symbol: str, price_data: pd.DataFrame) -> None:
        """Synchronous storage of historical prices."""
        try:
            # Prepare data for BigQuery
            df = price_data.copy()
            df['symbol'] = symbol
            df['created_at'] = datetime.now()
            
            # Rename columns to match BigQuery schema
            column_mapping = {
                'Date': 'date',
                'Open': 'open_price',
                'High': 'high_price', 
                'Low': 'low_price',
                'Close': 'close_price',
                'Volume': 'volume',
                'Adj Close': 'adjusted_close'
            }
            df = df.rename(columns=column_mapping)
            
            # Ensure date column is properly formatted
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Insert data into BigQuery
            table_ref = self.client.dataset(self.dataset_id).table('historical_prices')
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()  # Wait for job to complete
            
            logger.info(f"Stored {len(df)} historical price records for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to store historical prices for {symbol}: {e}")
            raise
    
    async def store_analysis_result(self, analysis: AnalysisResult, current_price: Decimal) -> None:
        """Store analysis result in BigQuery for historical tracking."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._store_analysis_result_sync,
            analysis,
            current_price
        )
    
    def _store_analysis_result_sync(self, analysis: AnalysisResult, current_price: Decimal) -> None:
        """Synchronous storage of analysis result."""
        try:
            # Extract price targets
            target_3m = None
            target_1y = None
            
            for target in analysis.price_targets:
                if target.timeframe == '3M':
                    target_3m = float(target.target)
                elif target.timeframe == '1Y':
                    target_1y = float(target.target)
            
            # Prepare data
            data = {
                'symbol': analysis.symbol,
                'analysis_date': analysis.analysis_timestamp,
                'recommendation': analysis.recommendation.value,
                'confidence': analysis.confidence,
                'overall_score': analysis.overall_score,
                'fundamental_score': analysis.fundamental_score,
                'technical_score': analysis.technical_score,
                'price_at_analysis': float(current_price),
                'target_price_3m': target_3m,
                'target_price_1y': target_1y,
                'risk_level': analysis.risk_level.value,
                'strengths': analysis.strengths,
                'weaknesses': analysis.weaknesses,
                'risks': analysis.risks,
                'created_at': datetime.now()
            }
            
            # Insert into BigQuery
            table_ref = self.client.dataset(self.dataset_id).table('analysis_history')
            errors = self.client.insert_rows_json(table_ref, [data])
            
            if errors:
                logger.error(f"Failed to insert analysis result: {errors}")
                raise Exception(f"BigQuery insert errors: {errors}")
            
            logger.info(f"Stored analysis result for {analysis.symbol}")
            
        except Exception as e:
            logger.error(f"Failed to store analysis result: {e}")
            raise
    
    async def get_historical_prices(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Retrieve historical price data from BigQuery.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            DataFrame with historical price data
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_historical_prices_sync,
            symbol,
            start_date,
            end_date
        )
    
    def _get_historical_prices_sync(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Synchronous retrieval of historical prices."""
        try:
            query = f"""
            SELECT 
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                adjusted_close
            FROM `{self.settings.GCP_PROJECT_ID}.{self.dataset_id}.historical_prices`
            WHERE symbol = @symbol
            AND date BETWEEN @start_date AND @end_date
            ORDER BY date ASC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("symbol", "STRING", symbol),
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.date()),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.date()),
                ]
            )
            
            df = self.client.query(query, job_config=job_config).to_dataframe()
            
            if df.empty:
                logger.warning(f"No historical data found for {symbol} between {start_date} and {end_date}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve historical prices for {symbol}: {e}")
            raise
    
    async def get_analysis_history(
        self, 
        symbol: str, 
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical analysis results for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Optional start date filter
            limit: Maximum number of results to return
            
        Returns:
            List of analysis history records
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_analysis_history_sync,
            symbol,
            start_date,
            limit
        )
    
    def _get_analysis_history_sync(
        self, 
        symbol: str, 
        start_date: Optional[datetime],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Synchronous retrieval of analysis history."""
        try:
            base_query = f"""
            SELECT *
            FROM `{self.settings.GCP_PROJECT_ID}.{self.dataset_id}.analysis_history`
            WHERE symbol = @symbol
            """
            
            parameters = [bigquery.ScalarQueryParameter("symbol", "STRING", symbol)]
            
            if start_date:
                base_query += " AND analysis_date >= @start_date"
                parameters.append(
                    bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date)
                )
            
            base_query += " ORDER BY analysis_date DESC LIMIT @limit"
            parameters.append(bigquery.ScalarQueryParameter("limit", "INTEGER", limit))
            
            job_config = bigquery.QueryJobConfig(query_parameters=parameters)
            
            results = self.client.query(base_query, job_config=job_config)
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis history for {symbol}: {e}")
            raise
    
    async def store_backtest_results(self, backtest_results: List[Dict[str, Any]]) -> None:
        """Store backtesting results in BigQuery."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._store_backtest_results_sync,
            backtest_results
        )
    
    def _store_backtest_results_sync(self, backtest_results: List[Dict[str, Any]]) -> None:
        """Synchronous storage of backtest results."""
        try:
            if not backtest_results:
                return
            
            # Add created_at timestamp to all records
            for result in backtest_results:
                result['created_at'] = datetime.now()
            
            table_ref = self.client.dataset(self.dataset_id).table('backtest_results')
            errors = self.client.insert_rows_json(table_ref, backtest_results)
            
            if errors:
                logger.error(f"Failed to insert backtest results: {errors}")
                raise Exception(f"BigQuery insert errors: {errors}")
            
            logger.info(f"Stored {len(backtest_results)} backtest results")
            
        except Exception as e:
            logger.error(f"Failed to store backtest results: {e}")
            raise
    
    async def get_backtest_results(
        self, 
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve backtest results with optional filters."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_backtest_results_sync,
            strategy_name,
            symbol,
            start_date,
            end_date
        )
    
    def _get_backtest_results_sync(
        self,
        strategy_name: Optional[str],
        symbol: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Synchronous retrieval of backtest results."""
        try:
            base_query = f"""
            SELECT *
            FROM `{self.settings.GCP_PROJECT_ID}.{self.dataset_id}.backtest_results`
            WHERE 1=1
            """
            
            parameters = []
            
            if strategy_name:
                base_query += " AND strategy_name = @strategy_name"
                parameters.append(
                    bigquery.ScalarQueryParameter("strategy_name", "STRING", strategy_name)
                )
            
            if symbol:
                base_query += " AND symbol = @symbol"
                parameters.append(
                    bigquery.ScalarQueryParameter("symbol", "STRING", symbol)
                )
            
            if start_date:
                base_query += " AND start_date >= @start_date"
                parameters.append(
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date.date())
                )
            
            if end_date:
                base_query += " AND end_date <= @end_date"
                parameters.append(
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.date())
                )
            
            base_query += " ORDER BY created_at DESC"
            
            job_config = bigquery.QueryJobConfig(query_parameters=parameters)
            results = self.client.query(base_query, job_config=job_config)
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to retrieve backtest results: {e}")
            raise
    
    async def cleanup_old_data(self, days_to_keep: int = 365) -> None:
        """Clean up old data to manage storage costs."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._cleanup_old_data_sync, days_to_keep)
    
    def _cleanup_old_data_sync(self, days_to_keep: int) -> None:
        """Synchronous cleanup of old data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean up old backtest results (keep analysis_history and historical_prices)
            query = f"""
            DELETE FROM `{self.settings.GCP_PROJECT_ID}.{self.dataset_id}.backtest_results`
            WHERE created_at < @cutoff_date
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("cutoff_date", "TIMESTAMP", cutoff_date)
                ]
            )
            
            job = self.client.query(query, job_config=job_config)
            job.result()
            
            logger.info(f"Cleaned up backtest results older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise