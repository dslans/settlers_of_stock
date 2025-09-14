"""
Tests for Alert API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from app.models.alert import Alert, AlertType, AlertStatus
from app.models.user import User
from app.schemas.alert import AlertCreate, PriceAlertQuickCreate


@pytest.fixture
def client():
    """Test client for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = User()
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_alert():
    """Mock alert instance."""
    alert = Alert()
    alert.id = 1
    alert.user_id = 1
    alert.symbol = "AAPL"
    alert.alert_type = AlertType.PRICE_ABOVE
    alert.status = AlertStatus.ACTIVE
    alert.condition_value = Decimal("150.00")
    alert.condition_operator = ">="
    alert.name = "AAPL Above $150"
    alert.description = "Test alert"
    alert.notify_email = True
    alert.notify_push = True
    alert.notify_sms = False
    alert.max_triggers = 1
    alert.trigger_count = 0
    alert.cooldown_minutes = 60
    alert.created_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    return alert


class TestAlertAPI:
    """Test cases for Alert API endpoints."""

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_create_alert_success(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test successful alert creation."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_alert.return_value = mock_alert
            mock_service_class.return_value = mock_service
            
            # Request data
            alert_data = {
                "symbol": "AAPL",
                "alert_type": "price_above",
                "condition_value": 150.00,
                "condition_operator": ">=",
                "name": "AAPL Above $150",
                "description": "Test alert",
                "notification_settings": {
                    "email": True,
                    "push": True,
                    "sms": False
                },
                "max_triggers": 1,
                "cooldown_minutes": 60
            }
            
            # Make request
            response = client.post("/api/v1/alerts/", json=alert_data)
            
            # Verify response
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["name"] == "AAPL Above $150"
            assert data["alert_type"] == "price_above"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_create_quick_price_alert(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test quick price alert creation."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_alert.return_value = mock_alert
            mock_service_class.return_value = mock_service
            
            # Request data
            quick_alert_data = {
                "symbol": "AAPL",
                "target_price": 150.00,
                "alert_when": "above",
                "name": "AAPL Above $150"
            }
            
            # Make request
            response = client.post("/api/v1/alerts/quick-price", json=quick_alert_data)
            
            # Verify response
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["symbol"] == "AAPL"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_user_alerts(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test retrieving user alerts."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_alerts.return_value = [mock_alert]
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.get("/api/v1/alerts/")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_user_alerts_with_filter(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test retrieving user alerts with status filter."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_alerts.return_value = [mock_alert]
            mock_service_class.return_value = mock_service
            
            # Make request with filter
            response = client.get("/api/v1/alerts/?status_filter=active")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            
            # Verify service was called with filter
            mock_service.get_user_alerts.assert_called_once_with(mock_user, AlertStatus.ACTIVE)

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_alert_stats(self, mock_get_db, mock_get_user, client, mock_user):
        """Test retrieving alert statistics."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_stats = {
                "total_alerts": 5,
                "active_alerts": 3,
                "paused_alerts": 1,
                "triggered_alerts": 1,
                "recent_triggers": []
            }
            mock_service.get_user_alert_stats.return_value = mock_stats
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.get("/api/v1/alerts/stats")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_alerts"] == 5
            assert data["active_alerts"] == 3

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_alert_by_id(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test retrieving specific alert by ID."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_alert_by_id.return_value = mock_alert
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.get("/api/v1/alerts/1")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == 1
            assert data["symbol"] == "AAPL"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_update_alert(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test updating an alert."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Update alert properties for return value
        mock_alert.name = "Updated Alert Name"
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_alert.return_value = mock_alert
            mock_service_class.return_value = mock_service
            
            # Request data
            update_data = {
                "name": "Updated Alert Name",
                "condition_value": 160.00
            }
            
            # Make request
            response = client.put("/api/v1/alerts/1", json=update_data)
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Updated Alert Name"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_delete_alert(self, mock_get_db, mock_get_user, client, mock_user):
        """Test deleting an alert."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.delete_alert.return_value = None
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.delete("/api/v1/alerts/1")
            
            # Verify response
            assert response.status_code == status.HTTP_204_NO_CONTENT

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_pause_alert(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test pausing an alert."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Update alert status for return value
        mock_alert.status = AlertStatus.PAUSED
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.pause_alert.return_value = mock_alert
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post("/api/v1/alerts/1/pause")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "paused"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_resume_alert(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test resuming an alert."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Update alert status for return value
        mock_alert.status = AlertStatus.ACTIVE
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.resume_alert.return_value = mock_alert
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post("/api/v1/alerts/1/resume")
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "active"

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_test_alert(self, mock_get_db, mock_get_user, client, mock_user, mock_alert):
        """Test testing an alert's conditions."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_alert_by_id.return_value = mock_alert
            mock_service.check_alert_conditions.return_value = {
                "trigger_value": 155.00,
                "condition": "Price $155.00 >= $150.00",
                "market_price": 155.00
            }
            mock_service.data_service.get_market_data.return_value = MagicMock(
                price=Decimal("155.00"),
                change=Decimal("5.00"),
                change_percent=Decimal("3.33"),
                volume=50000000
            )
            mock_service_class.return_value = mock_service
            
            # Request data
            test_data = {
                "alert_id": 1,
                "force_trigger": False
            }
            
            # Make request
            response = client.post("/api/v1/alerts/1/test", json=test_data)
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["alert_id"] == 1
            assert data["would_trigger"] == True
            assert "Price $155.00 >= $150.00" in data["trigger_reason"]

    @patch('app.core.dependencies.get_current_user')
    @patch('app.core.database.get_db')
    def test_test_notifications(self, mock_get_db, mock_get_user, client, mock_user):
        """Test testing notification delivery."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock notification service
        with patch('app.services.notification_service.NotificationService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.test_notification_delivery.return_value = {
                "email": True,
                "push": True,
                "sms": False
            }
            mock_service_class.return_value = mock_service
            
            # Request data
            test_data = {
                "notification_types": ["email", "push"]
            }
            
            # Make request
            response = client.post("/api/v1/alerts/test-notifications", json=test_data)
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["results"]["email"] == True
            assert data["results"]["push"] == True
            assert "email" not in data["results"] or "sms" not in data["results"]

    @patch('app.core.dependencies.get_current_user')
    def test_create_bulk_alerts(self, mock_get_user, client, mock_user):
        """Test creating multiple alerts at once."""
        # Mock dependencies
        mock_get_user.return_value = mock_user
        
        # Mock alert service
        with patch('app.api.alerts.AlertService') as mock_service_class:
            mock_service = AsyncMock()
            
            # Mock successful creation for first alert, failure for second
            def mock_create_alert(user, alert_data):
                if alert_data.symbol == "AAPL":
                    alert = Alert()
                    alert.id = 1
                    alert.symbol = "AAPL"
                    alert.name = alert_data.name
                    return alert
                else:
                    raise Exception("Invalid symbol")
            
            mock_service.create_alert.side_effect = mock_create_alert
            mock_service_class.return_value = mock_service
            
            # Request data
            bulk_data = {
                "alerts": [
                    {
                        "symbol": "AAPL",
                        "alert_type": "price_above",
                        "condition_value": 150.00,
                        "name": "AAPL Alert"
                    },
                    {
                        "symbol": "INVALID",
                        "alert_type": "price_above",
                        "condition_value": 100.00,
                        "name": "Invalid Alert"
                    }
                ]
            }
            
            # Make request
            response = client.post("/api/v1/alerts/bulk", json=bulk_data)
            
            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_created"] == 1
            assert data["total_failed"] == 1
            assert len(data["created_alerts"]) == 1
            assert len(data["failed_alerts"]) == 1

    def test_create_alert_validation_error(self, client):
        """Test alert creation with validation errors."""
        # Invalid request data (missing required fields)
        alert_data = {
            "symbol": "",  # Empty symbol
            "alert_type": "price_above",
            # Missing condition_value and name
        }
        
        # Make request without authentication
        response = client.post("/api/v1/alerts/", json=alert_data)
        
        # Should return validation error (422) or authentication error (401)
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_401_UNAUTHORIZED]

    def test_unauthorized_access(self, client):
        """Test accessing alerts without authentication."""
        # Make request without authentication
        response = client.get("/api/v1/alerts/")
        
        # Should return authentication error
        assert response.status_code == status.HTTP_401_UNAUTHORIZED