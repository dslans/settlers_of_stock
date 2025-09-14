"""
Tests for Alert Service functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.alert_service import AlertService
from app.models.alert import Alert, AlertTrigger, AlertType, AlertStatus
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertUpdate, NotificationSettings


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    user = User()
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def alert_service(mock_db):
    """Alert service instance with mocked dependencies."""
    service = AlertService(mock_db)
    service.data_service = AsyncMock()
    service.notification_service = AsyncMock()
    return service


@pytest.fixture
def sample_alert_create():
    """Sample alert creation data."""
    return AlertCreate(
        symbol="AAPL",
        alert_type=AlertType.PRICE_ABOVE,
        condition_value=Decimal("150.00"),
        condition_operator=">=",
        name="AAPL Above $150",
        description="Alert when Apple stock goes above $150",
        notification_settings=NotificationSettings(
            email=True,
            push=True,
            sms=False
        ),
        max_triggers=1,
        cooldown_minutes=60
    )


@pytest.fixture
def sample_alert():
    """Sample alert instance."""
    alert = Alert()
    alert.id = 1
    alert.user_id = 1
    alert.symbol = "AAPL"
    alert.alert_type = AlertType.PRICE_ABOVE
    alert.status = AlertStatus.ACTIVE
    alert.condition_value = Decimal("150.00")
    alert.condition_operator = ">="
    alert.name = "AAPL Above $150"
    alert.description = "Alert when Apple stock goes above $150"
    alert.notify_email = True
    alert.notify_push = True
    alert.notify_sms = False
    alert.max_triggers = 1
    alert.trigger_count = 0
    alert.cooldown_minutes = 60
    alert.created_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    return alert


class TestAlertService:
    """Test cases for AlertService."""

    @pytest.mark.asyncio
    async def test_create_alert_success(self, alert_service, mock_user, sample_alert_create, mock_db):
        """Test successful alert creation."""
        # Mock stock validation
        alert_service.data_service.get_stock_info.return_value = MagicMock(name="Apple Inc.")
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Create alert
        result = await alert_service.create_alert(mock_user, sample_alert_create)
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify alert properties
        added_alert = mock_db.add.call_args[0][0]
        assert added_alert.user_id == mock_user.id
        assert added_alert.symbol == "AAPL"
        assert added_alert.alert_type == AlertType.PRICE_ABOVE
        assert added_alert.condition_value == Decimal("150.00")
        assert added_alert.name == "AAPL Above $150"
        assert added_alert.status == AlertStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_alert_invalid_symbol(self, alert_service, mock_user, sample_alert_create):
        """Test alert creation with invalid stock symbol."""
        from app.services.data_aggregation import DataAggregationException
        
        # Mock invalid symbol
        alert_service.data_service.get_stock_info.side_effect = DataAggregationException(
            "INVALID_SYMBOL", "Invalid symbol", ["AAPL", "MSFT"]
        )
        
        # Should raise HTTPException
        with pytest.raises(Exception) as exc_info:
            await alert_service.create_alert(mock_user, sample_alert_create)
        
        assert "Invalid stock symbol" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_alerts(self, alert_service, mock_user, mock_db):
        """Test retrieving user alerts."""
        from sqlalchemy import select
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [sample_alert()]
        mock_db.execute.return_value = mock_result
        
        # Get alerts
        alerts = await alert_service.get_user_alerts(mock_user)
        
        # Verify query was executed
        mock_db.execute.assert_called_once()
        assert len(alerts) == 1

    @pytest.mark.asyncio
    async def test_check_alert_conditions_price_above_triggered(self, alert_service, sample_alert):
        """Test alert condition checking for price above trigger."""
        # Mock market data
        market_data = MagicMock()
        market_data.price = Decimal("155.00")  # Above threshold
        alert_service.data_service.get_market_data.return_value = market_data
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(sample_alert)
        
        # Should trigger
        assert trigger_data is not None
        assert trigger_data["trigger_value"] == 155.00
        assert "Price $155.00 >= $150.00" in trigger_data["condition"]

    @pytest.mark.asyncio
    async def test_check_alert_conditions_price_above_not_triggered(self, alert_service, sample_alert):
        """Test alert condition checking for price above not triggered."""
        # Mock market data
        market_data = MagicMock()
        market_data.price = Decimal("145.00")  # Below threshold
        alert_service.data_service.get_market_data.return_value = market_data
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(sample_alert)
        
        # Should not trigger
        assert trigger_data is None

    @pytest.mark.asyncio
    async def test_check_alert_conditions_inactive_alert(self, alert_service, sample_alert):
        """Test that inactive alerts are not checked."""
        sample_alert.status = AlertStatus.PAUSED
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(sample_alert)
        
        # Should not trigger
        assert trigger_data is None

    @pytest.mark.asyncio
    async def test_check_alert_conditions_expired_alert(self, alert_service, sample_alert, mock_db):
        """Test that expired alerts are marked as expired."""
        sample_alert.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(sample_alert)
        
        # Should not trigger and alert should be expired
        assert trigger_data is None
        assert sample_alert.status == AlertStatus.EXPIRED
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_alert_conditions_cooldown(self, alert_service, sample_alert):
        """Test that alerts in cooldown are not triggered."""
        sample_alert.last_triggered_at = datetime.utcnow() - timedelta(minutes=30)  # 30 min ago
        sample_alert.cooldown_minutes = 60  # 60 min cooldown
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(sample_alert)
        
        # Should not trigger due to cooldown
        assert trigger_data is None

    @pytest.mark.asyncio
    async def test_check_alert_conditions_max_triggers_reached(self, alert_service, sample_alert, mock_db):
        """Test that alerts with max triggers reached are expired."""
        sample_alert.trigger_count = 1
        sample_alert.max_triggers = 1
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(sample_alert)
        
        # Should not trigger and alert should be expired
        assert trigger_data is None
        assert sample_alert.status == AlertStatus.EXPIRED
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_alert(self, alert_service, sample_alert, mock_db):
        """Test alert triggering."""
        trigger_data = {
            "trigger_value": 155.00,
            "condition": "Price $155.00 >= $150.00",
            "market_price": 155.00
        }
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock notification service
        alert_service.notification_service.send_email_alert = AsyncMock(return_value=True)
        alert_service.notification_service.send_push_notification = AsyncMock(return_value=True)
        
        # Trigger alert
        alert_trigger = await alert_service.trigger_alert(sample_alert, trigger_data)
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_once()
        
        # Verify alert was updated
        assert sample_alert.trigger_count == 1
        assert sample_alert.last_triggered_at is not None
        
        # Verify notifications were sent
        alert_service.notification_service.send_email_alert.assert_called_once()
        alert_service.notification_service.send_push_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_alert(self, alert_service, mock_user, sample_alert, mock_db):
        """Test alert updating."""
        # Mock get_alert_by_id
        alert_service.get_alert_by_id = AsyncMock(return_value=sample_alert)
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Update data
        update_data = AlertUpdate(
            name="Updated Alert Name",
            condition_value=Decimal("160.00")
        )
        
        # Update alert
        result = await alert_service.update_alert(mock_user, sample_alert.id, update_data)
        
        # Verify updates
        assert sample_alert.name == "Updated Alert Name"
        assert sample_alert.condition_value == Decimal("160.00")
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_alert(self, alert_service, mock_user, sample_alert, mock_db):
        """Test alert deletion."""
        # Mock get_alert_by_id
        alert_service.get_alert_by_id = AsyncMock(return_value=sample_alert)
        
        # Mock database operations
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # Delete alert
        await alert_service.delete_alert(mock_user, sample_alert.id)
        
        # Verify deletion
        mock_db.delete.assert_called_once_with(sample_alert)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_alert(self, alert_service, mock_user, sample_alert, mock_db):
        """Test alert pausing."""
        # Mock get_alert_by_id
        alert_service.get_alert_by_id = AsyncMock(return_value=sample_alert)
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Pause alert
        result = await alert_service.pause_alert(mock_user, sample_alert.id)
        
        # Verify status change
        assert sample_alert.status == AlertStatus.PAUSED
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_alert(self, alert_service, mock_user, sample_alert, mock_db):
        """Test alert resuming."""
        sample_alert.status = AlertStatus.PAUSED
        
        # Mock get_alert_by_id
        alert_service.get_alert_by_id = AsyncMock(return_value=sample_alert)
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Resume alert
        result = await alert_service.resume_alert(mock_user, sample_alert.id)
        
        # Verify status change
        assert sample_alert.status == AlertStatus.ACTIVE
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_alerts_batch(self, alert_service, mock_db):
        """Test batch alert processing."""
        from sqlalchemy import select
        
        # Create sample alerts
        alerts = [sample_alert() for _ in range(3)]
        for i, alert in enumerate(alerts):
            alert.id = i + 1
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = alerts
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Mock check_alert_conditions to trigger one alert
        async def mock_check_conditions(alert):
            if alert.id == 1:
                return {
                    "trigger_value": 155.00,
                    "condition": "Test condition",
                    "market_price": 155.00
                }
            return None
        
        alert_service.check_alert_conditions = mock_check_conditions
        alert_service.trigger_alert = AsyncMock()
        
        # Process batch
        result = await alert_service.process_alerts_batch([1, 2, 3])
        
        # Verify results
        assert result["processed"] == 3
        assert result["triggered"] == 1
        assert result["errors"] == 0
        
        # Verify trigger_alert was called once
        alert_service.trigger_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_volume_spike_alert(self, alert_service):
        """Test volume spike alert condition."""
        # Create volume spike alert
        alert = Alert()
        alert.alert_type = AlertType.VOLUME_SPIKE
        alert.condition_value = Decimal("2.0")  # 2x average volume
        alert.status = AlertStatus.ACTIVE
        alert.symbol = "AAPL"
        
        # Mock market data with volume spike
        market_data = MagicMock()
        market_data.volume = 100000000  # 100M volume
        market_data.avg_volume = 40000000  # 40M average = 2.5x spike
        alert_service.data_service.get_market_data.return_value = market_data
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(alert)
        
        # Should trigger
        assert trigger_data is not None
        assert trigger_data["trigger_value"] == 2.5
        assert "Volume spike 2.5x >= 2.0x average" in trigger_data["condition"]

    @pytest.mark.asyncio
    async def test_price_change_percent_alert(self, alert_service):
        """Test price change percentage alert condition."""
        # Create price change alert
        alert = Alert()
        alert.alert_type = AlertType.PRICE_CHANGE_PERCENT
        alert.condition_value = Decimal("5.0")  # 5% change
        alert.status = AlertStatus.ACTIVE
        alert.symbol = "AAPL"
        
        # Mock market data with large price change
        market_data = MagicMock()
        market_data.price = Decimal("150.00")
        market_data.change_percent = Decimal("7.5")  # 7.5% change
        alert_service.data_service.get_market_data.return_value = market_data
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(alert)
        
        # Should trigger
        assert trigger_data is not None
        assert trigger_data["trigger_value"] == 7.5
        assert "Price change 7.5% >= 5.0%" in trigger_data["condition"]