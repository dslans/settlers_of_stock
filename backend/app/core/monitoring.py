"""
Monitoring and performance tracking utilities for Settlers of Stock.
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import contextmanager
from datetime import datetime

from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import TimeSeries, Point, TimeInterval
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.client = None
        self.project_name = None
        
        if settings.environment in ["production", "staging"]:
            try:
                self.client = monitoring_v3.MetricServiceClient()
                self.project_name = f"projects/{settings.GCP_PROJECT_ID}"
            except Exception as e:
                logger.warning(f"Could not initialize monitoring client: {e}")
    
    def record_custom_metric(
        self, 
        metric_type: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a custom metric to Google Cloud Monitoring."""
        if not self.client or not self.project_name:
            return
        
        try:
            # Create the metric descriptor if it doesn't exist
            metric_name = f"custom.googleapis.com/settlers_of_stock/{metric_type}"
            
            # Create time series data
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10 ** 9)
            interval = TimeInterval(
                {
                    "end_time": {"seconds": seconds, "nanos": nanos}
                }
            )
            point = Point(
                {
                    "interval": interval,
                    "value": {"double_value": value}
                }
            )
            
            series = TimeSeries()
            series.metric.type = metric_name
            series.resource.type = "gae_app"
            series.resource.labels["project_id"] = settings.GCP_PROJECT_ID
            series.resource.labels["module_id"] = "default"
            series.resource.labels["version_id"] = "1"
            
            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = val
            
            series.points = [point]
            
            # Write the time series data
            self.client.create_time_series(
                name=self.project_name, 
                time_series=[series]
            )
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_type}: {e}")
    
    def record_api_call_duration(
        self, 
        endpoint: str, 
        duration: float, 
        status_code: int
    ) -> None:
        """Record API call duration and status."""
        self.record_custom_metric(
            "api_call_duration",
            duration,
            {
                "endpoint": endpoint,
                "status_code": str(status_code)
            }
        )
    
    def record_external_api_call(
        self, 
        service: str, 
        duration: float, 
        success: bool
    ) -> None:
        """Record external API call metrics."""
        self.record_custom_metric(
            "external_api_duration",
            duration,
            {
                "service": service,
                "success": str(success).lower()
            }
        )
    
    def record_analysis_duration(
        self, 
        analysis_type: str, 
        symbol: str, 
        duration: float
    ) -> None:
        """Record stock analysis duration."""
        self.record_custom_metric(
            "analysis_duration",
            duration,
            {
                "analysis_type": analysis_type,
                "symbol": symbol
            }
        )
    
    def record_cache_hit_rate(
        self, 
        cache_type: str, 
        hit_rate: float
    ) -> None:
        """Record cache hit rate."""
        self.record_custom_metric(
            "cache_hit_rate",
            hit_rate,
            {
                "cache_type": cache_type
            }
        )
    
    def record_user_action(
        self, 
        action: str, 
        user_id: Optional[str] = None
    ) -> None:
        """Record user action for analytics."""
        labels = {"action": action}
        if user_id:
            labels["user_id"] = user_id
        
        self.record_custom_metric("user_actions", 1.0, labels)


# Global monitor instance
monitor = PerformanceMonitor()


def track_performance(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                monitor.record_custom_metric(
                    f"{metric_name}_duration",
                    duration,
                    labels
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = (labels or {}).copy()
                error_labels["error"] = str(type(e).__name__)
                monitor.record_custom_metric(
                    f"{metric_name}_error_duration",
                    duration,
                    error_labels
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                monitor.record_custom_metric(
                    f"{metric_name}_duration",
                    duration,
                    labels
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = (labels or {}).copy()
                error_labels["error"] = str(type(e).__name__)
                monitor.record_custom_metric(
                    f"{metric_name}_error_duration",
                    duration,
                    error_labels
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def track_operation(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager to track operation performance."""
    start_time = time.time()
    try:
        yield
        duration = time.time() - start_time
        monitor.record_custom_metric(
            f"{operation_name}_duration",
            duration,
            labels
        )
    except Exception as e:
        duration = time.time() - start_time
        error_labels = (labels or {}).copy()
        error_labels["error"] = str(type(e).__name__)
        monitor.record_custom_metric(
            f"{operation_name}_error_duration",
            duration,
            error_labels
        )
        raise


class RequestMetrics:
    """Middleware for tracking request metrics."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_duration = 0.0
    
    async def track_request(self, request, call_next):
        """Track request metrics."""
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            self.total_duration += duration
            
            # Record metrics
            monitor.record_api_call_duration(
                str(request.url.path),
                duration,
                response.status_code
            )
            
            if response.status_code >= 400:
                self.error_count += 1
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.total_duration += duration
            self.error_count += 1
            
            monitor.record_api_call_duration(
                str(request.url.path),
                duration,
                500
            )
            
            raise


# Global request metrics instance
request_metrics = RequestMetrics()


def log_performance_summary():
    """Log performance summary statistics."""
    if request_metrics.request_count > 0:
        avg_duration = request_metrics.total_duration / request_metrics.request_count
        error_rate = request_metrics.error_count / request_metrics.request_count
        
        logger.info(
            f"Performance Summary - "
            f"Requests: {request_metrics.request_count}, "
            f"Avg Duration: {avg_duration:.3f}s, "
            f"Error Rate: {error_rate:.2%}"
        )
        
        # Record summary metrics
        monitor.record_custom_metric("avg_request_duration", avg_duration)
        monitor.record_custom_metric("error_rate", error_rate)


class HealthChecker:
    """Health check utilities for monitoring."""
    
    @staticmethod
    async def check_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            from ..core.database import get_db
            
            start_time = time.time()
            # Simple query to test connection
            db = next(get_db())
            result = db.execute("SELECT 1").fetchone()
            duration = time.time() - start_time
            
            return {
                "status": "healthy" if result else "unhealthy",
                "response_time": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def check_redis_health() -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            import redis
            from ..core.config import get_settings
            
            settings = get_settings()
            if not settings.REDIS_URL:
                return {
                    "status": "not_configured",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            start_time = time.time()
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def check_external_apis_health() -> Dict[str, Any]:
        """Check external API connectivity."""
        try:
            import aiohttp
            
            apis_status = {}
            
            # Check Yahoo Finance (via yfinance)
            try:
                import yfinance as yf
                start_time = time.time()
                ticker = yf.Ticker("AAPL")
                info = ticker.info
                duration = time.time() - start_time
                
                apis_status["yahoo_finance"] = {
                    "status": "healthy" if info else "unhealthy",
                    "response_time": duration
                }
            except Exception as e:
                apis_status["yahoo_finance"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            return {
                "status": "healthy",
                "apis": apis_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global health checker instance
health_checker = HealthChecker()