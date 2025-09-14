"""
Celery tasks for alert processing and monitoring.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from ..core.config import get_settings
from ..core.database import db_manager
from ..services.alert_service import AlertService
from ..models.alert import Alert, AlertStatus

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery
celery_app = Celery(
    "settlers_of_stock_alerts",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.alert_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    'process-alerts-every-minute': {
        'task': 'app.tasks.alert_tasks.process_all_alerts',
        'schedule': 60.0,  # Run every minute
    },
    'cleanup-expired-alerts-hourly': {
        'task': 'app.tasks.alert_tasks.cleanup_expired_alerts',
        'schedule': 3600.0,  # Run every hour
    },
    'alert-system-health-check': {
        'task': 'app.tasks.alert_tasks.alert_system_health_check',
        'schedule': 300.0,  # Run every 5 minutes
    },
}


async def get_async_db_session():
    """Get async database session for tasks."""
    await db_manager.initialize_database()
    async for session in db_manager.get_async_session():
        return session


@celery_app.task(bind=True, name="app.tasks.alert_tasks.process_all_alerts")
def process_all_alerts(self):
    """Process all active alerts."""
    try:
        logger.info("Starting alert processing task")
        
        # Run the async function
        result = asyncio.run(_process_all_alerts_async())
        
        logger.info(f"Alert processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in process_all_alerts task: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _process_all_alerts_async():
    """Async implementation of alert processing."""
    try:
        db = await get_async_db_session()
        alert_service = AlertService(db)
        
        # Get all active alerts
        active_alerts = await alert_service.get_active_alerts()
        
        if not active_alerts:
            return {"message": "No active alerts to process", "processed": 0}
        
        # Process alerts in batches
        batch_size = 50
        total_processed = 0
        total_triggered = 0
        total_errors = 0
        
        for i in range(0, len(active_alerts), batch_size):
            batch = active_alerts[i:i + batch_size]
            alert_ids = [alert.id for alert in batch]
            
            try:
                batch_result = await alert_service.process_alerts_batch(alert_ids)
                total_processed += batch_result["processed"]
                total_triggered += batch_result["triggered"]
                total_errors += batch_result["errors"]
                
                logger.info(f"Processed batch {i//batch_size + 1}: {batch_result}")
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                total_errors += len(batch)
        
        result = {
            "total_alerts": len(active_alerts),
            "processed": total_processed,
            "triggered": total_triggered,
            "errors": total_errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in _process_all_alerts_async: {e}")
        raise


@celery_app.task(bind=True, name="app.tasks.alert_tasks.process_alert_batch")
def process_alert_batch(self, alert_ids: List[int]):
    """Process a specific batch of alerts."""
    try:
        logger.info(f"Processing alert batch: {alert_ids}")
        
        result = asyncio.run(_process_alert_batch_async(alert_ids))
        
        logger.info(f"Batch processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in process_alert_batch task: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=3)


async def _process_alert_batch_async(alert_ids: List[int]):
    """Async implementation of batch alert processing."""
    try:
        db = await get_async_db_session()
        alert_service = AlertService(db)
        
        result = await alert_service.process_alerts_batch(alert_ids)
        return result
        
    except Exception as e:
        logger.error(f"Error in _process_alert_batch_async: {e}")
        raise


@celery_app.task(bind=True, name="app.tasks.alert_tasks.process_single_alert")
def process_single_alert(self, alert_id: int):
    """Process a single alert immediately."""
    try:
        logger.info(f"Processing single alert: {alert_id}")
        
        result = asyncio.run(_process_single_alert_async(alert_id))
        
        logger.info(f"Single alert processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in process_single_alert task: {e}")
        raise self.retry(exc=e, countdown=10, max_retries=2)


async def _process_single_alert_async(alert_id: int):
    """Async implementation of single alert processing."""
    try:
        db = await get_async_db_session()
        alert_service = AlertService(db)
        
        # Get the alert
        from sqlalchemy import select
        query = select(Alert).where(Alert.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return {"error": f"Alert {alert_id} not found"}
        
        if alert.status != AlertStatus.ACTIVE:
            return {"message": f"Alert {alert_id} is not active", "status": alert.status.value}
        
        # Check conditions
        trigger_data = await alert_service.check_alert_conditions(alert)
        
        if trigger_data:
            # Trigger the alert
            alert_trigger = await alert_service.trigger_alert(alert, trigger_data)
            return {
                "alert_id": alert_id,
                "triggered": True,
                "trigger_id": alert_trigger.id,
                "condition": trigger_data.get("condition"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Update last checked time
            alert.last_checked_at = datetime.utcnow()
            await db.commit()
            
            return {
                "alert_id": alert_id,
                "triggered": False,
                "message": "Conditions not met",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error in _process_single_alert_async: {e}")
        raise


@celery_app.task(bind=True, name="app.tasks.alert_tasks.cleanup_expired_alerts")
def cleanup_expired_alerts(self):
    """Clean up expired and old triggered alerts."""
    try:
        logger.info("Starting alert cleanup task")
        
        result = asyncio.run(_cleanup_expired_alerts_async())
        
        logger.info(f"Alert cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_alerts task: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


async def _cleanup_expired_alerts_async():
    """Async implementation of alert cleanup."""
    try:
        db = await get_async_db_session()
        
        from sqlalchemy import select, update, and_, or_
        
        now = datetime.utcnow()
        
        # Mark expired alerts
        expired_query = update(Alert).where(
            and_(
                Alert.expires_at <= now,
                Alert.status == AlertStatus.ACTIVE
            )
        ).values(status=AlertStatus.EXPIRED)
        
        expired_result = await db.execute(expired_query)
        expired_count = expired_result.rowcount
        
        # Mark alerts that have reached max triggers
        max_triggers_query = update(Alert).where(
            and_(
                Alert.trigger_count >= Alert.max_triggers,
                Alert.status == AlertStatus.ACTIVE
            )
        ).values(status=AlertStatus.TRIGGERED)
        
        max_triggers_result = await db.execute(max_triggers_query)
        max_triggers_count = max_triggers_result.rowcount
        
        # Clean up old triggered alerts (older than 30 days)
        old_date = now - timedelta(days=30)
        old_alerts_query = select(Alert).where(
            and_(
                Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.EXPIRED]),
                Alert.updated_at <= old_date
            )
        )
        
        old_alerts_result = await db.execute(old_alerts_query)
        old_alerts = old_alerts_result.scalars().all()
        
        # Delete old alerts and their triggers
        deleted_count = 0
        for alert in old_alerts:
            await db.delete(alert)
            deleted_count += 1
        
        await db.commit()
        
        result = {
            "expired_alerts": expired_count,
            "max_triggers_reached": max_triggers_count,
            "deleted_old_alerts": deleted_count,
            "timestamp": now.isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in _cleanup_expired_alerts_async: {e}")
        raise


@celery_app.task(bind=True, name="app.tasks.alert_tasks.alert_system_health_check")
def alert_system_health_check(self):
    """Perform health check on the alert system."""
    try:
        logger.info("Starting alert system health check")
        
        result = asyncio.run(_alert_system_health_check_async())
        
        logger.info(f"Alert system health check completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in alert_system_health_check task: {e}")
        return {"status": "error", "error": str(e)}


async def _alert_system_health_check_async():
    """Async implementation of alert system health check."""
    try:
        db = await get_async_db_session()
        
        from sqlalchemy import select, func
        
        # Count alerts by status
        status_counts = {}
        for status in AlertStatus:
            count_query = select(func.count(Alert.id)).where(Alert.status == status)
            count_result = await db.execute(count_query)
            status_counts[status.value] = count_result.scalar()
        
        # Check for alerts that haven't been checked recently
        stale_threshold = datetime.utcnow() - timedelta(minutes=10)
        stale_query = select(func.count(Alert.id)).where(
            and_(
                Alert.status == AlertStatus.ACTIVE,
                or_(
                    Alert.last_checked_at.is_(None),
                    Alert.last_checked_at <= stale_threshold
                )
            )
        )
        stale_result = await db.execute(stale_query)
        stale_count = stale_result.scalar()
        
        # Check recent trigger activity
        recent_threshold = datetime.utcnow() - timedelta(hours=1)
        recent_triggers_query = select(func.count(Alert.id)).where(
            Alert.last_triggered_at >= recent_threshold
        )
        recent_triggers_result = await db.execute(recent_triggers_query)
        recent_triggers_count = recent_triggers_result.scalar()
        
        health_status = "healthy"
        issues = []
        
        if stale_count > 0:
            issues.append(f"{stale_count} alerts haven't been checked recently")
            if stale_count > 100:
                health_status = "degraded"
        
        if status_counts.get("active", 0) > 10000:
            issues.append("High number of active alerts may impact performance")
            health_status = "warning"
        
        result = {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "alert_counts": status_counts,
            "stale_alerts": stale_count,
            "recent_triggers": recent_triggers_count,
            "issues": issues
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in _alert_system_health_check_async: {e}")
        raise


# Utility functions for manual task execution

def trigger_alert_processing():
    """Manually trigger alert processing."""
    return process_all_alerts.delay()


def trigger_alert_cleanup():
    """Manually trigger alert cleanup."""
    return cleanup_expired_alerts.delay()


def process_user_alerts(user_id: int):
    """Process alerts for a specific user."""
    # This would need to be implemented to filter alerts by user
    pass


def get_task_status(task_id: str):
    """Get the status of a Celery task."""
    return celery_app.AsyncResult(task_id)


# Task monitoring and metrics

@celery_app.task(bind=True, name="app.tasks.alert_tasks.get_alert_processing_metrics")
def get_alert_processing_metrics(self):
    """Get metrics about alert processing performance."""
    try:
        result = asyncio.run(_get_alert_processing_metrics_async())
        return result
    except Exception as e:
        logger.error(f"Error getting alert processing metrics: {e}")
        return {"error": str(e)}


async def _get_alert_processing_metrics_async():
    """Get alert processing metrics."""
    try:
        db = await get_async_db_session()
        
        from sqlalchemy import select, func
        from ..models.alert import AlertTrigger
        
        # Metrics for the last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        # Count triggers in last 24 hours
        triggers_query = select(func.count(AlertTrigger.id)).where(
            AlertTrigger.triggered_at >= last_24h
        )
        triggers_result = await db.execute(triggers_query)
        triggers_24h = triggers_result.scalar()
        
        # Count successful notifications
        email_success_query = select(func.count(AlertTrigger.id)).where(
            and_(
                AlertTrigger.triggered_at >= last_24h,
                AlertTrigger.email_sent == True
            )
        )
        email_success_result = await db.execute(email_success_query)
        email_success_24h = email_success_result.scalar()
        
        push_success_query = select(func.count(AlertTrigger.id)).where(
            and_(
                AlertTrigger.triggered_at >= last_24h,
                AlertTrigger.push_sent == True
            )
        )
        push_success_result = await db.execute(push_success_query)
        push_success_24h = push_success_result.scalar()
        
        return {
            "period": "24_hours",
            "alerts_triggered": triggers_24h,
            "email_notifications_sent": email_success_24h,
            "push_notifications_sent": push_success_24h,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in _get_alert_processing_metrics_async: {e}")
        raise