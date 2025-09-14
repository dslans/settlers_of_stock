"""
Tests for earnings API endpoints.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.earnings import (
    EarningsEvent, CorporateEvent,
    EventType, EarningsConfidence, EventImpact,
    EarningsCalendarResponse, CorporateEventsResponse,
    EarningsImpactAnalysis
)
from app.services.earnings_service import EarningsServiceException


class TestEarningsAPI:
    """Test cases for earnings API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_earnings_event_data(self):
        """Sample earnings event data."""
        return {
            "id": 1,
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "earnings_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "report_time": "AMC",
            "fiscal_quarter": "Q1",
            "fiscal_year": 2024,
            "eps_estimate": 1.50,
            "revenue_estimate": 90000000000,
            "confidence": "high",
            "impact_level": "high",
            "is_confirmed": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "days_until_earnings": 7,
            "is_upcoming": True,
            "has_estimates": True,
            "has_actuals": False
        }
    
    @pytest.fixture
    def sample_corporate_event_data(self):
        """Sample corporate event data."""
        return {
            "id": 1,
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "event_type": "dividend",
            "event_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "dividend_amount": 0.25,
            "impact_level": "low",
            "is_confirmed": True,
            "description": "Quarterly dividend payment",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "days_until_event": 14,
            "is_upcoming": True
        }
    
    @pytest.fixture
    def mock_earnings_service(self):
        """Mock earnings service."""
        return Mock()

    def test_get_earnings_calendar_success(self, client, sample_earnings_event_data):
        """Test successful earnings calendar retrieval."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_earnings_event_data],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=30)}
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/calendar",
                    params={
                        "symbols": "AAPL",
                        "start_date": date.today().isoformat(),
                        "end_date": (date.today() + timedelta(days=30)).isoformat(),
                        "limit": 100
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 1
        assert data["upcoming_events"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["symbol"] == "AAPL"

    def test_get_corporate_events_calendar_success(self, client, sample_corporate_event_data):
        """Test successful corporate events calendar retrieval."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = CorporateEventsResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_corporate_event_data],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=30)},
                event_types=[EventType.DIVIDEND]
            )
            mock_service.get_corporate_events_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/events",
                    params={
                        "symbols": "AAPL",
                        "event_types": "dividend",
                        "start_date": date.today().isoformat(),
                        "end_date": (date.today() + timedelta(days=30)).isoformat(),
                        "limit": 100
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 1
        assert data["upcoming_events"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["symbol"] == "AAPL"
        assert data["events"][0]["event_type"] == "dividend"

    def test_get_upcoming_earnings_for_symbol_success(self, client, sample_earnings_event_data):
        """Test successful upcoming earnings retrieval for symbol."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_earnings_event_data],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=90)}
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/AAPL/upcoming",
                    params={"days_ahead": 90}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["is_upcoming"] is True

    def test_get_corporate_events_for_symbol_success(self, client, sample_corporate_event_data):
        """Test successful corporate events retrieval for symbol."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = CorporateEventsResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_corporate_event_data],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=90)},
                event_types=[EventType.DIVIDEND]
            )
            mock_service.get_corporate_events_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/AAPL/events",
                    params={"days_ahead": 90, "event_types": "dividend"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["event_type"] == "dividend"

    def test_get_earnings_impact_analysis_success(self, client):
        """Test successful earnings impact analysis retrieval."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_analysis = EarningsImpactAnalysis(
                symbol="AAPL",
                upcoming_earnings=None,
                historical_performance=[],
                avg_price_change_1d=Decimal("2.5"),
                avg_price_change_1w=Decimal("1.8"),
                beat_rate=Decimal("75.0"),
                expected_volatility="medium",
                risk_level="medium",
                key_metrics_to_watch=["EPS", "Revenue", "Guidance"]
            )
            mock_service.get_earnings_impact_analysis = AsyncMock(return_value=mock_analysis)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get("/earnings/AAPL/impact-analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["avg_price_change_1d"] == 2.5
        assert data["beat_rate"] == 75.0
        assert data["expected_volatility"] == "medium"
        assert "EPS" in data["key_metrics_to_watch"]

    def test_fetch_earnings_data_success(self, client, sample_earnings_event_data, sample_corporate_event_data):
        """Test successful earnings data fetching."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and methods
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_service.fetch_earnings_data_for_symbol = AsyncMock(
                return_value=[sample_earnings_event_data]
            )
            mock_service.fetch_corporate_events_for_symbol = AsyncMock(
                return_value=[sample_corporate_event_data]
            )
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.post(
                    "/earnings/AAPL/fetch-data",
                    params={"days_ahead": 90}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully fetched data for AAPL" in data["message"]
        assert data["earnings_events_count"] == 1
        assert data["corporate_events_count"] == 1
        assert len(data["earnings_events"]) == 1
        assert len(data["corporate_events"]) == 1

    def test_get_todays_earnings_success(self, client, sample_earnings_event_data):
        """Test successful today's earnings retrieval."""
        # Modify sample data to be today
        today_earnings = sample_earnings_event_data.copy()
        today_earnings["earnings_date"] = datetime.now().replace(hour=16, minute=0).isoformat()
        today_earnings["days_until_earnings"] = 0
        
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=1,
                upcoming_events=1,
                events=[today_earnings],
                date_range={"start_date": date.today(), "end_date": date.today()}
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get("/earnings/today")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["days_until_earnings"] == 0

    def test_get_this_weeks_earnings_success(self, client, sample_earnings_event_data):
        """Test successful this week's earnings retrieval."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_earnings_event_data],
                date_range={
                    "start_date": date.today() - timedelta(days=date.today().weekday()),
                    "end_date": date.today() + timedelta(days=6-date.today().weekday())
                }
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get("/earnings/this-week")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 1
        assert len(data["events"]) == 1

    def test_earnings_calendar_with_filters(self, client, sample_earnings_event_data):
        """Test earnings calendar with various filters."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_earnings_event_data],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=30)}
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/calendar",
                    params={
                        "symbols": "AAPL,GOOGL,MSFT",
                        "confirmed_only": "true",
                        "impact_levels": "high,medium",
                        "has_estimates": "true",
                        "limit": 50,
                        "offset": 10
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] >= 0

    def test_corporate_events_with_filters(self, client, sample_corporate_event_data):
        """Test corporate events calendar with various filters."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = CorporateEventsResponse(
                total_events=1,
                upcoming_events=1,
                events=[sample_corporate_event_data],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=30)},
                event_types=[EventType.DIVIDEND]
            )
            mock_service.get_corporate_events_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/events",
                    params={
                        "symbols": "AAPL,GOOGL",
                        "event_types": "dividend,stock_split",
                        "confirmed_only": "true",
                        "impact_levels": "high,medium,low",
                        "limit": 25
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] >= 0

    def test_earnings_service_exception_handling(self, client):
        """Test earnings service exception handling."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method to raise exception
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_service.get_earnings_calendar = AsyncMock(
                side_effect=EarningsServiceException(
                    "Data fetch failed",
                    error_type="DATA_FETCH_ERROR",
                    suggestions=["Try again later", "Check symbol"]
                )
            )
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get("/earnings/calendar")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["message"] == "Data fetch failed"
        assert data["detail"]["error_type"] == "DATA_FETCH_ERROR"
        assert "Try again later" in data["detail"]["suggestions"]

    def test_invalid_symbol_format(self, client):
        """Test handling of invalid symbol format."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method to raise exception
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_service.get_earnings_calendar = AsyncMock(
                side_effect=EarningsServiceException(
                    "Invalid symbol format",
                    error_type="INVALID_SYMBOL",
                    suggestions=["Check symbol spelling", "Use standard format"]
                )
            )
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get("/earnings/INVALID123/upcoming")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_type"] == "INVALID_SYMBOL"

    def test_unauthorized_access(self, client):
        """Test unauthorized access to earnings endpoints."""
        # Mock authentication to raise exception
        with patch('app.api.earnings.get_current_user', side_effect=Exception("Unauthorized")):
            response = client.get("/earnings/calendar")
        
        # Should return 500 due to unhandled auth exception
        # In real implementation, this would be handled by auth middleware
        assert response.status_code == 500

    def test_parameter_validation(self, client):
        """Test parameter validation."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_earnings_calendar = AsyncMock(return_value=EarningsCalendarResponse(
                total_events=0, upcoming_events=0, events=[], date_range={}
            ))
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                # Test invalid limit (too high)
                response = client.get(
                    "/earnings/calendar",
                    params={"limit": 1000}  # Exceeds max limit of 500
                )
        
        assert response.status_code == 422  # Validation error

    def test_date_range_validation(self, client):
        """Test date range parameter validation."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_earnings_calendar = AsyncMock(return_value=EarningsCalendarResponse(
                total_events=0, upcoming_events=0, events=[], date_range={}
            ))
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/calendar",
                    params={
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31"
                    }
                )
        
        assert response.status_code == 200

    def test_empty_results(self, client):
        """Test handling of empty results."""
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=0,
                upcoming_events=0,
                events=[],
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=30)}
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get("/earnings/calendar")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 0
        assert data["upcoming_events"] == 0
        assert len(data["events"]) == 0

    def test_large_dataset_pagination(self, client, sample_earnings_event_data):
        """Test pagination with large datasets."""
        # Create multiple events
        events = []
        for i in range(50):
            event = sample_earnings_event_data.copy()
            event["id"] = i + 1
            event["symbol"] = f"STOCK{i:02d}"
            events.append(event)
        
        with patch('app.api.earnings.EarningsService') as mock_service_class:
            # Mock service instance and method
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_calendar_response = EarningsCalendarResponse(
                total_events=50,
                upcoming_events=50,
                events=events[:25],  # First page
                date_range={"start_date": date.today(), "end_date": date.today() + timedelta(days=30)}
            )
            mock_service.get_earnings_calendar = AsyncMock(return_value=mock_calendar_response)
            
            # Mock authentication
            with patch('app.api.earnings.get_current_user', return_value=Mock()):
                response = client.get(
                    "/earnings/calendar",
                    params={"limit": 25, "offset": 0}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 50
        assert len(data["events"]) == 25


if __name__ == "__main__":
    pytest.main([__file__])