"""
Alert API endpoints for managing price alerts and notifications.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..models.alert import AlertStatus
from ..services.alert_service import AlertService
from ..schemas.alert import (
    AlertCreate, AlertUpdate, AlertResponse, AlertListResponse,
    AlertStatsResponse, AlertBulkCreateRequest, AlertBulkCreateResponse,
    AlertTestRequest, AlertTestResponse, PriceAlertQuickCreate,
    AlertNotificationTest, AlertNotificationTestResponse
)
from ..tasks.alert_tasks import process_single_alert, trigger_alert_processing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert."""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.create_alert(current_user, alert_data)
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


@router.post("/quick-price", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_price_alert(
    quick_alert: PriceAlertQuickCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a quick price alert (above or below a target price)."""
    try:
        from ..models.alert import AlertType
        
        # Convert quick alert to full alert
        alert_type = AlertType.PRICE_ABOVE if quick_alert.alert_when == "above" else AlertType.PRICE_BELOW
        condition_operator = ">=" if quick_alert.alert_when == "above" else "<="
        
        alert_data = AlertCreate(
            symbol=quick_alert.symbol,
            alert_type=alert_type,
            condition_value=quick_alert.target_price,
            condition_operator=condition_operator,
            name=quick_alert.name or f"{quick_alert.symbol} {quick_alert.alert_when} ${quick_alert.target_price}",
            description=f"Quick price alert for {quick_alert.symbol} when price goes {quick_alert.alert_when} ${quick_alert.target_price}"
        )
        
        alert_service = AlertService(db)
        alert = await alert_service.create_alert(current_user, alert_data)
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating quick price alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quick price alert"
        )


@router.post("/bulk", response_model=AlertBulkCreateResponse)
async def create_bulk_alerts(
    bulk_request: AlertBulkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple alerts at once."""
    try:
        alert_service = AlertService(db)
        
        created_alerts = []
        failed_alerts = []
        
        for alert_data in bulk_request.alerts:
            try:
                alert = await alert_service.create_alert(current_user, alert_data)
                created_alerts.append(alert)
            except Exception as e:
                failed_alerts.append({
                    "symbol": alert_data.symbol,
                    "name": alert_data.name,
                    "error": str(e)
                })
        
        return AlertBulkCreateResponse(
            created_alerts=created_alerts,
            failed_alerts=failed_alerts,
            total_created=len(created_alerts),
            total_failed=len(failed_alerts)
        )
        
    except Exception as e:
        logger.error(f"Error creating bulk alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk alerts"
        )


@router.get("/", response_model=List[AlertResponse])
async def get_user_alerts(
    status_filter: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts for the current user."""
    try:
        alert_service = AlertService(db)
        alerts = await alert_service.get_user_alerts(current_user, status_filter)
        return alerts
    except Exception as e:
        logger.error(f"Error getting user alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get alert statistics for the current user."""
    try:
        alert_service = AlertService(db)
        stats = await alert_service.get_user_alert_stats(current_user)
        return stats
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert statistics"
        )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert by ID."""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.get_alert_by_id(current_user, alert_id)
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert"
        )


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    update_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an alert."""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.update_alert(current_user, alert_id, update_data)
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert."""
    try:
        alert_service = AlertService(db)
        await alert_service.delete_alert(current_user, alert_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )


@router.post("/{alert_id}/pause", response_model=AlertResponse)
async def pause_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause an alert."""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.pause_alert(current_user, alert_id)
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause alert"
        )


@router.post("/{alert_id}/resume", response_model=AlertResponse)
async def resume_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused alert."""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.resume_alert(current_user, alert_id)
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume alert"
        )


@router.post("/{alert_id}/test", response_model=AlertTestResponse)
async def test_alert(
    alert_id: int,
    test_request: AlertTestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test an alert's conditions."""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.get_alert_by_id(current_user, alert_id)
        
        # Check current conditions
        trigger_data = await alert_service.check_alert_conditions(alert)
        
        would_trigger = trigger_data is not None
        trigger_reason = trigger_data.get("condition") if trigger_data else "Conditions not met"
        
        # If force_trigger is True and conditions are met, trigger the alert
        if test_request.force_trigger and would_trigger:
            background_tasks.add_task(process_single_alert.delay, alert_id)
        
        # Get current market data for context
        try:
            market_data = await alert_service.data_service.get_market_data(alert.symbol)
            current_conditions = {
                "current_price": float(market_data.price),
                "daily_change": float(market_data.change),
                "daily_change_percent": float(market_data.change_percent),
                "volume": market_data.volume
            }
        except Exception:
            current_conditions = {"error": "Could not fetch current market data"}
        
        return AlertTestResponse(
            alert_id=alert_id,
            symbol=alert.symbol,
            current_conditions=current_conditions,
            would_trigger=would_trigger,
            trigger_reason=trigger_reason,
            test_timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test alert"
        )


@router.post("/test-notifications", response_model=AlertNotificationTestResponse)
async def test_notifications(
    test_request: AlertNotificationTest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test notification delivery for the current user."""
    try:
        from ..services.notification_service import NotificationService
        
        notification_service = NotificationService()
        results = await notification_service.test_notification_delivery(current_user.id)
        
        # Filter results based on requested types
        filtered_results = {
            notification_type: results.get(notification_type, False)
            for notification_type in test_request.notification_types
        }
        
        success_count = sum(1 for success in filtered_results.values() if success)
        total_count = len(filtered_results)
        
        message = f"Notification test completed: {success_count}/{total_count} successful"
        
        return AlertNotificationTestResponse(
            results=filtered_results,
            timestamp=datetime.utcnow(),
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test notifications"
        )


# Admin/system endpoints (would typically require admin permissions)

@router.post("/system/process-all")
async def trigger_alert_processing_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Manually trigger alert processing for all users."""
    try:
        # In a real implementation, you'd check for admin permissions here
        task = trigger_alert_processing()
        
        return {
            "message": "Alert processing triggered",
            "task_id": task.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering alert processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger alert processing"
        )


@router.get("/system/health")
async def get_alert_system_health():
    """Get alert system health status."""
    try:
        from ..tasks.alert_tasks import alert_system_health_check
        
        # Run health check
        task = alert_system_health_check.delay()
        result = task.get(timeout=30)  # Wait up to 30 seconds
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting alert system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert system health"
        )


# WebSocket endpoint for real-time alert updates (placeholder)
# This would be implemented in the websocket.py file

from datetime import datetime