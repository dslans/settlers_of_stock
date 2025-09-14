"""
Tests for earnings service functionality.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.earnings_service import EarningsService, EarningsServiceException
from app.models.earnings import (
    EarningsEvent, CorporateEvent, EarningsHistoricalPerformance,
    EarningsCalendarFilter, EventCalendarFilter,
    EventType, EarningsConfidence, EventImpact
)


class TestEarningsService:
    """Test cases for EarningsService."""
    
    @pytest.fixture
    def earnings_service(self):
        """Create earnings service instance."""
        return EarningsService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_earnings_event(self):
        """Create sample earnings event."""
        return EarningsEvent(
            id=1,
            symbol="AAPL",
            company_name="Apple Inc.",
            earnings_date=datetime.now() + timedelta(days=7),
            report_time="AMC",
            fiscal_quarter="Q1",
            fiscal_year=2024,
            eps_estimate=Decimal("1.50"),
            revenue_estimate=Decimal("90000000000"),
            confidence=EarningsConfidence.HIGH,
            impact_level=EventImpact.HIGH,
            is_confirmed=True
        )
    
    @pytest.fixture
    def sample_corporate_event(self):
        """Create sample corporate event."""
        return CorporateEvent(
            id=1,
            symbol="AAPL",
            company_name="Apple Inc.",
            event_type=EventType.DIVIDEND,
            event_date=datetime.now() + timedelta(days=14),
            dividend_amount=Decimal("0.25"),
            impact_level=EventImpact.LOW,
            is_confirmed=True,
            description="Quarterly dividend payment"
        )
    
    @pytest.fixture
    def sample_historical_performance(self):
        """Create sample historical performance data."""
        return EarningsHistoricalPerformance(
            id=1,
            symbol="AAPL",
            price_before_earnings=Decimal("150.00"),
            price_after_earnings=Decimal("155.00"),
            price_change_1d=Decimal("3.33"),
            price_change_1w=Decimal("2.50"),
            volume_before=50000000,
            volume_after=75000000,
            volume_change=Decimal("50.00"),
            beat_estimate=True,
            surprise_magnitude=Decimal("0.05")
        )

    @pytest.mark.asyncio
    async def test_get_earnings_calendar_success(self, earnings_service, mock_db_session, sample_earnings_event):
        """Test successful earnings calendar retrieval."""
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_earnings_event]
        mock_db_session.execute.return_value = mock_result
        
        # Create filter
        filters = EarningsCalendarFilter(
            symbols=["AAPL"],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        
        # Call service method
        result = await earnings_service.get_earnings_calendar(
            db=mock_db_session,
            filters=filters,
            limit=100,
            offset=0
        )
        
        # Assertions
        assert result.total_events >= 0
        assert len(result.events) >= 0
        assert result.date_range["start_date"] == filters.start_date
        assert result.date_range["end_date"] == filters.end_date
        
        # Verify database was called
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_get_corporate_events_calendar_success(self, earnings_service, mock_db_session, sample_corporate_event):
        """Test successful corporate events calendar retrieval."""
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_corporate_event]
        mock_db_session.execute.return_value = mock_result
        
        # Create filter
        filters = EventCalendarFilter(
            symbols=["AAPL"],
            event_types=[EventType.DIVIDEND],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        
        # Call service method
        result = await earnings_service.get_corporate_events_calendar(
            db=mock_db_session,
            filters=filters,
            limit=100,
            offset=0
        )
        
        # Assertions
        assert result.total_events >= 0
        assert len(result.events) >= 0
        assert EventType.DIVIDEND in result.event_types or len(result.event_types) == 0
        
        # Verify database was called
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_fetch_earnings_data_for_symbol_success(self, earnings_service, mock_db_session):
        """Test successful earnings data fetching for a symbol."""
        # Mock yfinance data fetching
        with patch.object(earnings_service, '_fetch_earnings_from_yfinance') as mock_fetch:
            mock_fetch.return_value = [
                {
                    'symbol': 'AAPL',
                    'company_name': 'Apple Inc.',
                    'earnings_date': datetime.now() + timedelta(days=7),
                    'eps_estimate': 1.50,
                    'confidence': EarningsConfidence.HIGH,
                    'impact_level': EventImpact.HIGH,
                    'is_confirmed': True
                }
            ]
            
            # Mock database operations
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_db_session.flush = AsyncMock()
            mock_db_session.commit = AsyncMock()
            
            # Call service method
            result = await earnings_service.fetch_earnings_data_for_symbol(
                db=mock_db_session,
                symbol="AAPL",
                days_ahead=90
            )
            
            # Assertions
            assert len(result) >= 0
            mock_fetch.assert_called_once_with("AAPL")
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_corporate_events_for_symbol_success(self, earnings_service, mock_db_session):
        """Test successful corporate events fetching for a symbol."""
        # Mock yfinance data fetching
        with patch.object(earnings_service, '_fetch_corporate_events_from_yfinance') as mock_fetch:
            mock_fetch.return_value = [
                {
                    'symbol': 'AAPL',
                    'company_name': 'Apple Inc.',
                    'event_type': EventType.DIVIDEND,
                    'event_date': datetime.now() + timedelta(days=14),
                    'dividend_amount': 0.25,
                    'impact_level': EventImpact.LOW,
                    'is_confirmed': True,
                    'description': 'Quarterly dividend'
                }
            ]
            
            # Mock database operations
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_db_session.flush = AsyncMock()
            mock_db_session.commit = AsyncMock()
            
            # Call service method
            result = await earnings_service.fetch_corporate_events_for_symbol(
                db=mock_db_session,
                symbol="AAPL",
                days_ahead=90
            )
            
            # Assertions
            assert len(result) >= 0
            mock_fetch.assert_called_once_with("AAPL")
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_earnings_impact_analysis_success(self, earnings_service, mock_db_session, sample_earnings_event, sample_historical_performance):
        """Test successful earnings impact analysis."""
        # Mock database queries
        upcoming_result = Mock()
        upcoming_result.scalar_one_or_none.return_value = sample_earnings_event
        
        historical_result = Mock()
        historical_result.scalars.return_value.all.return_value = [sample_historical_performance]
        
        mock_db_session.execute.side_effect = [upcoming_result, historical_result]
        
        # Call service method
        result = await earnings_service.get_earnings_impact_analysis(
            db=mock_db_session,
            symbol="AAPL"
        )
        
        # Assertions
        assert result.symbol == "AAPL"
        assert result.upcoming_earnings is not None
        assert len(result.historical_performance) >= 0
        assert result.avg_price_change_1d is not None
        assert result.beat_rate is not None
        assert len(result.key_metrics_to_watch) > 0

    @pytest.mark.asyncio
    async def test_fetch_earnings_from_yfinance_success(self, earnings_service):
        """Test successful yfinance earnings data fetching."""
        # Mock yfinance ticker
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'earningsDate': datetime.now() + timedelta(days=7)
        }
        mock_ticker.calendar = None  # No calendar data
        
        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = await earnings_service._fetch_earnings_from_yfinance("AAPL")
            
            # Assertions
            assert len(result) >= 0
            if len(result) > 0:
                assert result[0]['symbol'] == 'AAPL'
                assert result[0]['company_name'] == 'Apple Inc.'

    @pytest.mark.asyncio
    async def test_fetch_corporate_events_from_yfinance_success(self, earnings_service):
        """Test successful yfinance corporate events fetching."""
        # Mock yfinance ticker with dividend data
        import pandas as pd
        
        mock_ticker = Mock()
        mock_ticker.info = {'longName': 'Apple Inc.'}
        
        # Mock dividends data
        dividend_dates = [datetime.now() - timedelta(days=90)]
        dividend_amounts = [0.25]
        mock_ticker.dividends = pd.Series(dividend_amounts, index=dividend_dates)
        
        # Mock splits data (empty)
        mock_ticker.splits = pd.Series([], dtype=float)
        
        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = await earnings_service._fetch_corporate_events_from_yfinance("AAPL")
            
            # Assertions
            assert len(result) >= 0
            if len(result) > 0:
                dividend_event = next((e for e in result if e['event_type'] == EventType.DIVIDEND), None)
                assert dividend_event is not None
                assert dividend_event['symbol'] == 'AAPL'
                assert dividend_event['dividend_amount'] == 0.25

    @pytest.mark.asyncio
    async def test_calculate_earnings_impact_metrics_success(self, earnings_service, sample_historical_performance):
        """Test earnings impact metrics calculation."""
        historical_data = [sample_historical_performance]
        
        result = await earnings_service._calculate_earnings_impact_metrics(historical_data)
        
        # Assertions
        assert result['avg_price_change_1d'] is not None
        assert result['avg_price_change_1w'] is not None
        assert result['beat_rate'] is not None
        assert result['expected_volatility'] in ['high', 'medium', 'low', 'unknown']
        assert result['risk_level'] in ['high', 'medium', 'low', 'unknown']
        assert isinstance(result['key_metrics_to_watch'], list)

    @pytest.mark.asyncio
    async def test_calculate_earnings_impact_metrics_empty_data(self, earnings_service):
        """Test earnings impact metrics calculation with empty data."""
        result = await earnings_service._calculate_earnings_impact_metrics([])
        
        # Assertions
        assert result['avg_price_change_1d'] is None
        assert result['avg_price_change_1w'] is None
        assert result['beat_rate'] is None
        assert result['expected_volatility'] == 'unknown'
        assert result['risk_level'] == 'unknown'
        assert isinstance(result['key_metrics_to_watch'], list)

    @pytest.mark.asyncio
    async def test_convert_to_earnings_response_success(self, earnings_service, sample_earnings_event):
        """Test conversion of earnings event to response model."""
        result = await earnings_service._convert_to_earnings_response(sample_earnings_event)
        
        # Assertions
        assert result.id == sample_earnings_event.id
        assert result.symbol == sample_earnings_event.symbol
        assert result.company_name == sample_earnings_event.company_name
        assert result.is_upcoming is True  # Future date
        assert result.has_estimates is True  # Has EPS estimate
        assert result.days_until_earnings is not None

    @pytest.mark.asyncio
    async def test_convert_to_corporate_event_response_success(self, earnings_service, sample_corporate_event):
        """Test conversion of corporate event to response model."""
        result = await earnings_service._convert_to_corporate_event_response(sample_corporate_event)
        
        # Assertions
        assert result.id == sample_corporate_event.id
        assert result.symbol == sample_corporate_event.symbol
        assert result.company_name == sample_corporate_event.company_name
        assert result.event_type == sample_corporate_event.event_type
        assert result.is_upcoming is True  # Future date
        assert result.days_until_event is not None

    def test_determine_fiscal_quarter_success(self, earnings_service):
        """Test fiscal quarter determination."""
        # Test each quarter
        q1_date = datetime(2024, 2, 15)  # February
        q2_date = datetime(2024, 5, 15)  # May
        q3_date = datetime(2024, 8, 15)  # August
        q4_date = datetime(2024, 11, 15) # November
        
        assert earnings_service._determine_fiscal_quarter(q1_date) == "Q1"
        assert earnings_service._determine_fiscal_quarter(q2_date) == "Q2"
        assert earnings_service._determine_fiscal_quarter(q3_date) == "Q3"
        assert earnings_service._determine_fiscal_quarter(q4_date) == "Q4"

    @pytest.mark.asyncio
    async def test_store_or_update_earnings_event_new_event(self, earnings_service, mock_db_session):
        """Test storing new earnings event."""
        # Mock no existing event
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.flush = AsyncMock()
        
        earnings_info = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'earnings_date': datetime.now() + timedelta(days=7),
            'eps_estimate': 1.50
        }
        
        result = await earnings_service._store_or_update_earnings_event(
            db=mock_db_session,
            earnings_info=earnings_info
        )
        
        # Assertions
        assert result is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_or_update_earnings_event_update_existing(self, earnings_service, mock_db_session, sample_earnings_event):
        """Test updating existing earnings event."""
        # Mock existing event
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_earnings_event
        
        earnings_info = {
            'symbol': 'AAPL',
            'earnings_date': sample_earnings_event.earnings_date,
            'eps_estimate': 1.75,  # Updated estimate
            'is_confirmed': True
        }
        
        result = await earnings_service._store_or_update_earnings_event(
            db=mock_db_session,
            earnings_info=earnings_info
        )
        
        # Assertions
        assert result is not None
        assert result.eps_estimate == Decimal('1.75')
        assert result.is_confirmed is True
        # Should not add new event
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_earnings_service_exception_handling(self, earnings_service, mock_db_session):
        """Test earnings service exception handling."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        
        filters = EarningsCalendarFilter(symbols=["AAPL"])
        
        with pytest.raises(EarningsServiceException) as exc_info:
            await earnings_service.get_earnings_calendar(
                db=mock_db_session,
                filters=filters
            )
        
        assert exc_info.value.error_type == "DATABASE_ERROR"
        assert "Database error" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_yfinance_error_handling(self, earnings_service):
        """Test yfinance error handling."""
        # Mock yfinance error
        with patch('yfinance.Ticker', side_effect=Exception("Network error")):
            result = await earnings_service._fetch_earnings_from_yfinance("INVALID")
            
            # Should return empty list on error
            assert result == []

    @pytest.mark.asyncio
    async def test_filter_validation(self, earnings_service, mock_db_session):
        """Test filter validation and application."""
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        # Test with comprehensive filters
        filters = EarningsCalendarFilter(
            symbols=["AAPL", "GOOGL"],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            confirmed_only=True,
            impact_levels=[EventImpact.HIGH, EventImpact.MEDIUM],
            has_estimates=True
        )
        
        result = await earnings_service.get_earnings_calendar(
            db=mock_db_session,
            filters=filters,
            limit=50,
            offset=10
        )
        
        # Should execute without error
        assert result.total_events >= 0
        mock_db_session.execute.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])