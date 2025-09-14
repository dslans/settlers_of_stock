"""
Celery application configuration for Settlers of Stock.
"""

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "settlers_of_stock",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.alert_tasks"]
)

# Configuration
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

# Beat schedule for periodic tasks
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

if __name__ == "__main__":
    celery_app.start()