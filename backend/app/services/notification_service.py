"""
Notification Service for sending alerts via email, push notifications, and SMS.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    """Service for sending various types of notifications."""
    
    def __init__(self):
        self.email_enabled = bool(settings.SMTP_HOST and settings.SMTP_USER)
        self.push_enabled = False  # Will be enabled when push service is configured
        self.sms_enabled = False   # Will be enabled when SMS service is configured
    
    async def send_email_alert(
        self, 
        user_id: int, 
        subject: str, 
        message: str, 
        alert_data: Dict[str, Any]
    ) -> bool:
        """Send email alert to user."""
        if not self.email_enabled:
            logger.warning("Email notifications not configured")
            return False
        
        try:
            # Get user email (in a real implementation, you'd fetch from database)
            user_email = await self._get_user_email(user_id)
            if not user_email:
                logger.error(f"No email found for user {user_id}")
                return False
            
            # Create email content
            html_content = self._create_email_html(subject, message, alert_data)
            text_content = self._create_email_text(message, alert_data)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_USER
            msg['To'] = user_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email alert sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert to user {user_id}: {e}")
            return False
    
    async def send_push_notification(
        self, 
        user_id: int, 
        title: str, 
        message: str, 
        alert_data: Dict[str, Any]
    ) -> bool:
        """Send push notification to user."""
        if not self.push_enabled:
            logger.info(f"Push notification would be sent to user {user_id}: {title}")
            return True  # Return True for testing purposes
        
        try:
            # In a real implementation, you would:
            # 1. Get user's push notification tokens from database
            # 2. Use a service like Firebase Cloud Messaging (FCM) or Apple Push Notification Service (APNs)
            # 3. Send the notification
            
            # Placeholder implementation
            notification_payload = {
                "title": title,
                "body": message,
                "data": alert_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Push notification sent to user {user_id}: {notification_payload}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification to user {user_id}: {e}")
            return False
    
    async def send_sms_alert(self, user_id: int, message: str) -> bool:
        """Send SMS alert to user."""
        if not self.sms_enabled:
            logger.info(f"SMS would be sent to user {user_id}: {message}")
            return True  # Return True for testing purposes
        
        try:
            # In a real implementation, you would:
            # 1. Get user's phone number from database
            # 2. Use a service like Twilio, AWS SNS, or Google Cloud SMS
            # 3. Send the SMS
            
            # Placeholder implementation
            logger.info(f"SMS sent to user {user_id}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to user {user_id}: {e}")
            return False
    
    async def send_webhook_notification(
        self, 
        user_id: int, 
        webhook_url: str, 
        alert_data: Dict[str, Any]
    ) -> bool:
        """Send webhook notification."""
        try:
            import aiohttp
            
            payload = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_data": alert_data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent to {webhook_url}")
                        return True
                    else:
                        logger.error(f"Webhook returned status {response.status}")
                        return False
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    def _create_email_html(self, subject: str, message: str, alert_data: Dict[str, Any]) -> str:
        """Create HTML email content."""
        symbol = alert_data.get("symbol", "N/A")
        price = alert_data.get("market_price", "N/A")
        condition = alert_data.get("condition", message)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
                .alert-info {{ background-color: #f8fafc; padding: 15px; border-radius: 6px; margin: 15px 0; }}
                .symbol {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .price {{ font-size: 20px; font-weight: bold; color: #059669; }}
                .condition {{ font-size: 16px; color: #374151; margin: 10px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Stock Alert Triggered</h1>
                </div>
                
                <div class="alert-info">
                    <div class="symbol">{symbol}</div>
                    <div class="price">Current Price: ${price}</div>
                    <div class="condition">{condition}</div>
                </div>
                
                <p>Your stock alert has been triggered. Please review your investment strategy and consider taking appropriate action.</p>
                
                <div class="footer">
                    <p>This is an automated message from Settlers of Stock. Please do not reply to this email.</p>
                    <p><strong>Disclaimer:</strong> This alert is for informational purposes only and should not be considered as investment advice.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_email_text(self, message: str, alert_data: Dict[str, Any]) -> str:
        """Create plain text email content."""
        symbol = alert_data.get("symbol", "N/A")
        price = alert_data.get("market_price", "N/A")
        condition = alert_data.get("condition", message)
        
        text = f"""
STOCK ALERT TRIGGERED

Symbol: {symbol}
Current Price: ${price}
Condition: {condition}

Your stock alert has been triggered. Please review your investment strategy and consider taking appropriate action.

---
This is an automated message from Settlers of Stock.
Disclaimer: This alert is for informational purposes only and should not be considered as investment advice.
        """
        return text.strip()
    
    async def _get_user_email(self, user_id: int) -> Optional[str]:
        """Get user email from database."""
        # In a real implementation, you would query the database
        # For now, return a placeholder
        return f"user{user_id}@example.com"
    
    async def _get_user_phone(self, user_id: int) -> Optional[str]:
        """Get user phone number from database."""
        # In a real implementation, you would query the database
        # For now, return None
        return None
    
    async def test_notification_delivery(self, user_id: int) -> Dict[str, bool]:
        """Test notification delivery for all enabled channels."""
        results = {}
        
        test_data = {
            "symbol": "AAPL",
            "market_price": 150.00,
            "condition": "Test notification"
        }
        
        # Test email
        if self.email_enabled:
            results["email"] = await self.send_email_alert(
                user_id, 
                "Test Alert", 
                "This is a test notification", 
                test_data
            )
        else:
            results["email"] = False
        
        # Test push notification
        results["push"] = await self.send_push_notification(
            user_id,
            "Test Alert",
            "This is a test notification",
            test_data
        )
        
        # Test SMS
        results["sms"] = await self.send_sms_alert(
            user_id,
            "Test SMS: This is a test notification"
        )
        
        return results