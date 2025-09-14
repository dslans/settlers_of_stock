"""
Alert Service for managing price alerts and notifications.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, func, select, update
from fastapi import HTTPException, status

from ..models.alert import Alert, AlertTrigger, AlertType, AlertStatus
from ..models.user import User
from ..schemas.alert import (
    AlertCreate, AlertUpdate, AlertResponse, AlertTriggerResponse,
    AlertCondition, NotificationSettings
)
from .data_aggregation import DataAggregationService, DataAggregationException
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing alerts and alert processing."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_service = DataAggregationService()
        self.notification_service = NotificationService()
    
    # Alert CRUD operations
    
    async def create_alert(self, user: User, alert_data: AlertCreate) -> Alert:
        """Create a new alert for the user."""
        try:
            # Validate stock symbol
            symbol = alert_data.symbol.upper().strip()
            try:
                stock_info = await self.data_service.get_stock_info(symbol)
            except DataAggregationException as e:
                if e.error_type == "INVALID_SYMBOL":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid stock symbol: {symbol}. {', '.join(e.suggestions)}"
                    )
                else:
                    logger.warning(f"Could not validate symbol {symbol}, proceeding anyway")
            
            # Create alert
            alert = Alert(
                user_id=user.id,
                symbol=symbol,
                alert_type=alert_data.alert_type,
                condition_value=alert_data.condition_value,
                condition_operator=alert_data.condition_operator,
                name=alert_data.name,
                description=alert_data.description,
                message_template=alert_data.message_template,
                notify_email=alert_data.notification_settings.email if alert_data.notification_settings else True,
                notify_push=alert_data.notification_settings.push if alert_data.notification_settings else True,
                notify_sms=alert_data.notification_settings.sms if alert_data.notification_settings else False,
                expires_at=alert_data.expires_at,
                max_triggers=alert_data.max_triggers or 1,
                cooldown_minutes=alert_data.cooldown_minutes or 60,
                status=AlertStatus.ACTIVE
            )
            
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Created alert '{alert.name}' for {symbol} for user {user.id}")
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create alert for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create alert"
            )
    
    async def get_user_alerts(self, user: User, status_filter: Optional[AlertStatus] = None) -> List[Alert]:
        """Get all alerts for a user."""
        try:
            query = select(Alert).where(Alert.user_id == user.id)
            
            if status_filter:
                query = query.where(Alert.status == status_filter)
            
            query = query.order_by(desc(Alert.created_at))
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            
            return list(alerts)
            
        except Exception as e:
            logger.error(f"Failed to get alerts for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve alerts"
            )
    
    async def get_alert_by_id(self, user: User, alert_id: int) -> Alert:
        """Get a specific alert by ID."""
        try:
            query = select(Alert).where(
                and_(Alert.id == alert_id, Alert.user_id == user.id)
            )
            result = await self.db.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Alert not found"
                )
            
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get alert {alert_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve alert"
            )
    
    async def update_alert(self, user: User, alert_id: int, update_data: AlertUpdate) -> Alert:
        """Update an alert."""
        try:
            alert = await self.get_alert_by_id(user, alert_id)
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            
            # Handle notification settings
            if 'notification_settings' in update_dict:
                notification_settings = update_dict.pop('notification_settings')
                if notification_settings:
                    update_dict['notify_email'] = notification_settings.get('email', alert.notify_email)
                    update_dict['notify_push'] = notification_settings.get('push', alert.notify_push)
                    update_dict['notify_sms'] = notification_settings.get('sms', alert.notify_sms)
            
            for field, value in update_dict.items():
                setattr(alert, field, value)
            
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Updated alert {alert_id} for user {user.id}")
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update alert {alert_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update alert"
            )
    
    async def delete_alert(self, user: User, alert_id: int) -> None:
        """Delete an alert."""
        try:
            alert = await self.get_alert_by_id(user, alert_id)
            
            await self.db.delete(alert)
            await self.db.commit()
            
            logger.info(f"Deleted alert {alert_id} for user {user.id}")
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete alert {alert_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete alert"
            )
    
    async def pause_alert(self, user: User, alert_id: int) -> Alert:
        """Pause an alert."""
        try:
            alert = await self.get_alert_by_id(user, alert_id)
            alert.status = AlertStatus.PAUSED
            
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Paused alert {alert_id} for user {user.id}")
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to pause alert {alert_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to pause alert"
            )
    
    async def resume_alert(self, user: User, alert_id: int) -> Alert:
        """Resume a paused alert."""
        try:
            alert = await self.get_alert_by_id(user, alert_id)
            
            if alert.status == AlertStatus.PAUSED:
                alert.status = AlertStatus.ACTIVE
            
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Resumed alert {alert_id} for user {user.id}")
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to resume alert {alert_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resume alert"
            )
    
    # Alert processing and monitoring
    
    async def check_alert_conditions(self, alert: Alert) -> Optional[Dict[str, Any]]:
        """Check if an alert's conditions are met."""
        try:
            # Skip if alert is not active
            if alert.status != AlertStatus.ACTIVE:
                return None
            
            # Check if alert has expired
            if alert.expires_at and datetime.utcnow() > alert.expires_at:
                await self._expire_alert(alert)
                return None
            
            # Check if alert is in cooldown
            if alert.last_triggered_at and alert.cooldown_minutes > 0:
                cooldown_end = alert.last_triggered_at + timedelta(minutes=alert.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    return None
            
            # Check if alert has reached max triggers
            if alert.trigger_count >= alert.max_triggers:
                await self._expire_alert(alert)
                return None
            
            # Get current market data
            try:
                market_data = await self.data_service.get_market_data(alert.symbol)
            except DataAggregationException as e:
                logger.warning(f"Could not get market data for {alert.symbol}: {e}")
                return None
            
            # Check alert condition based on type
            trigger_data = None
            
            if alert.alert_type == AlertType.PRICE_ABOVE:
                if market_data.price >= alert.condition_value:
                    trigger_data = {
                        "trigger_value": float(market_data.price),
                        "condition": f"Price ${market_data.price} >= ${alert.condition_value}",
                        "market_price": float(market_data.price)
                    }
            
            elif alert.alert_type == AlertType.PRICE_BELOW:
                if market_data.price <= alert.condition_value:
                    trigger_data = {
                        "trigger_value": float(market_data.price),
                        "condition": f"Price ${market_data.price} <= ${alert.condition_value}",
                        "market_price": float(market_data.price)
                    }
            
            elif alert.alert_type == AlertType.PRICE_CHANGE_PERCENT:
                if abs(market_data.change_percent) >= alert.condition_value:
                    trigger_data = {
                        "trigger_value": float(market_data.change_percent),
                        "condition": f"Price change {market_data.change_percent}% >= {alert.condition_value}%",
                        "market_price": float(market_data.price)
                    }
            
            elif alert.alert_type == AlertType.VOLUME_SPIKE:
                # Check if volume is X times higher than average
                if hasattr(market_data, 'avg_volume') and market_data.avg_volume > 0:
                    volume_ratio = market_data.volume / market_data.avg_volume
                    if volume_ratio >= alert.condition_value:
                        trigger_data = {
                            "trigger_value": float(volume_ratio),
                            "condition": f"Volume spike {volume_ratio:.1f}x >= {alert.condition_value}x average",
                            "market_price": float(market_data.price)
                        }
            
            # Add more alert types as needed (technical indicators, etc.)
            
            return trigger_data
            
        except Exception as e:
            logger.error(f"Failed to check alert conditions for alert {alert.id}: {e}")
            return None
    
    async def trigger_alert(self, alert: Alert, trigger_data: Dict[str, Any]) -> AlertTrigger:
        """Trigger an alert and send notifications."""
        try:
            # Create alert trigger record
            alert_trigger = AlertTrigger(
                alert_id=alert.id,
                trigger_value=Decimal(str(trigger_data.get("trigger_value", 0))),
                market_price=Decimal(str(trigger_data.get("market_price", 0))),
                message=trigger_data.get("condition", "Alert condition met"),
                trigger_metadata=str(trigger_data)  # Store as JSON string
            )
            
            self.db.add(alert_trigger)
            
            # Update alert
            alert.trigger_count += 1
            alert.last_triggered_at = datetime.utcnow()
            alert.last_checked_at = datetime.utcnow()
            
            # Check if alert should be expired after this trigger
            if alert.trigger_count >= alert.max_triggers:
                alert.status = AlertStatus.TRIGGERED
            
            await self.db.commit()
            await self.db.refresh(alert_trigger)
            
            # Send notifications
            await self._send_alert_notifications(alert, alert_trigger, trigger_data)
            
            logger.info(f"Triggered alert {alert.id} for {alert.symbol}")
            return alert_trigger
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to trigger alert {alert.id}: {e}")
            raise
    
    async def _send_alert_notifications(self, alert: Alert, trigger: AlertTrigger, trigger_data: Dict[str, Any]) -> None:
        """Send notifications for a triggered alert."""
        try:
            # Prepare notification message
            if alert.message_template:
                message = alert.message_template.format(
                    symbol=alert.symbol,
                    condition=trigger_data.get("condition", "Alert condition met"),
                    price=trigger_data.get("market_price", "N/A"),
                    trigger_value=trigger_data.get("trigger_value", "N/A")
                )
            else:
                message = f"{alert.symbol}: {trigger_data.get('condition', 'Alert condition met')}"
            
            notification_results = {}
            
            # Send email notification
            if alert.notify_email:
                try:
                    await self.notification_service.send_email_alert(
                        user_id=alert.user_id,
                        subject=f"Stock Alert: {alert.symbol}",
                        message=message,
                        alert_data=trigger_data
                    )
                    notification_results["email"] = True
                    trigger.email_sent = True
                except Exception as e:
                    logger.error(f"Failed to send email for alert {alert.id}: {e}")
                    notification_results["email"] = False
            
            # Send push notification
            if alert.notify_push:
                try:
                    await self.notification_service.send_push_notification(
                        user_id=alert.user_id,
                        title=f"Stock Alert: {alert.symbol}",
                        message=message,
                        alert_data=trigger_data
                    )
                    notification_results["push"] = True
                    trigger.push_sent = True
                except Exception as e:
                    logger.error(f"Failed to send push notification for alert {alert.id}: {e}")
                    notification_results["push"] = False
            
            # Send SMS notification
            if alert.notify_sms:
                try:
                    await self.notification_service.send_sms_alert(
                        user_id=alert.user_id,
                        message=message
                    )
                    notification_results["sms"] = True
                    trigger.sms_sent = True
                except Exception as e:
                    logger.error(f"Failed to send SMS for alert {alert.id}: {e}")
                    notification_results["sms"] = False
            
            await self.db.commit()
            
            logger.info(f"Sent notifications for alert {alert.id}: {notification_results}")
            
        except Exception as e:
            logger.error(f"Failed to send notifications for alert {alert.id}: {e}")
    
    async def _expire_alert(self, alert: Alert) -> None:
        """Mark an alert as expired."""
        try:
            alert.status = AlertStatus.EXPIRED
            await self.db.commit()
            logger.info(f"Expired alert {alert.id}")
        except Exception as e:
            logger.error(f"Failed to expire alert {alert.id}: {e}")
    
    # Batch processing methods for Celery tasks
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts for processing."""
        try:
            query = select(Alert).where(Alert.status == AlertStatus.ACTIVE)
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            return list(alerts)
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def process_alerts_batch(self, alert_ids: List[int]) -> Dict[str, Any]:
        """Process a batch of alerts."""
        results = {
            "processed": 0,
            "triggered": 0,
            "errors": 0,
            "details": []
        }
        
        try:
            query = select(Alert).where(Alert.id.in_(alert_ids))
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            
            for alert in alerts:
                try:
                    # Update last checked time
                    alert.last_checked_at = datetime.utcnow()
                    
                    # Check conditions
                    trigger_data = await self.check_alert_conditions(alert)
                    
                    if trigger_data:
                        # Trigger the alert
                        await self.trigger_alert(alert, trigger_data)
                        results["triggered"] += 1
                        results["details"].append({
                            "alert_id": alert.id,
                            "symbol": alert.symbol,
                            "status": "triggered",
                            "condition": trigger_data.get("condition")
                        })
                    else:
                        results["details"].append({
                            "alert_id": alert.id,
                            "symbol": alert.symbol,
                            "status": "checked"
                        })
                    
                    results["processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing alert {alert.id}: {e}")
                    results["errors"] += 1
                    results["details"].append({
                        "alert_id": alert.id,
                        "symbol": alert.symbol,
                        "status": "error",
                        "error": str(e)
                    })
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process alerts batch: {e}")
            results["errors"] += len(alert_ids)
        
        return results
    
    # Statistics and reporting
    
    async def get_user_alert_stats(self, user: User) -> Dict[str, Any]:
        """Get statistics about user's alerts."""
        try:
            # Basic counts
            total_alerts_query = select(func.count(Alert.id)).where(Alert.user_id == user.id)
            total_alerts_result = await self.db.execute(total_alerts_query)
            total_alerts = total_alerts_result.scalar()
            
            active_alerts_query = select(func.count(Alert.id)).where(
                and_(Alert.user_id == user.id, Alert.status == AlertStatus.ACTIVE)
            )
            active_alerts_result = await self.db.execute(active_alerts_query)
            active_alerts = active_alerts_result.scalar()
            
            # Recent triggers
            recent_triggers_query = select(AlertTrigger).join(Alert).where(
                Alert.user_id == user.id
            ).order_by(desc(AlertTrigger.triggered_at)).limit(10)
            recent_triggers_result = await self.db.execute(recent_triggers_query)
            recent_triggers = recent_triggers_result.scalars().all()
            
            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "paused_alerts": 0,  # Could be calculated
                "triggered_alerts": 0,  # Could be calculated
                "recent_triggers": [
                    {
                        "alert_id": trigger.alert_id,
                        "triggered_at": trigger.triggered_at,
                        "message": trigger.message
                    }
                    for trigger in recent_triggers
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert stats for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve alert statistics"
            )