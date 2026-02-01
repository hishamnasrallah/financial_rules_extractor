"""
External service integrations for notifications and webhooks.
Supports Slack, Discord, Email, and generic webhooks.
"""
import json
import requests
from typing import Dict, Optional, List, Any
from datetime import datetime
from loguru import logger

from src.models import ExtractionResult, ExtractedRule
from src.config import config


class SlackIntegration:
    """Slack webhook and API integration."""
    
    def __init__(self, webhook_url: str, channel: str = None):
        """
        Initialize Slack integration.
        
        Args:
            webhook_url: Slack webhook URL
            channel: Default channel (optional)
        """
        self.webhook_url = webhook_url
        self.channel = channel or config.integrations.slack_channel
    
    def send_extraction_complete(self, result: ExtractionResult, document_name: str = None):
        """
        Send extraction completion notification to Slack.
        
        Args:
            result: Extraction result
            document_name: Name of processed document
        """
        try:
            # Build message blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Financial Rules Extraction Complete",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Document:*\n{document_name or result.document_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Processing Time:*\n{result.processing_time_seconds:.2f}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Rules Extracted:*\n{result.statistics.get('total_rules', 0)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Gaps Found:*\n{result.statistics.get('total_gaps', 0)}"
                        }
                    ]
                }
            ]
            
            # Add track breakdown
            rules_by_track = result.statistics.get('rules_by_track', {})
            if rules_by_track:
                track_text = "\n".join([
                    f"• {track}: {count}" 
                    for track, count in rules_by_track.items()
                    if count > 0
                ])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Rules by Track:*\n{track_text}"
                    }
                })
            
            payload = {
                "channel": self.channel,
                "blocks": blocks
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def send_message(self, message: str, channel: str = None):
        """
        Send a simple text message to Slack.
        
        Args:
            message: Message text
            channel: Channel to send to (optional)
        """
        try:
            payload = {
                "channel": channel or self.channel,
                "text": message
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack message sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")


class DiscordIntegration:
    """Discord webhook integration."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Discord integration.
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
    
    def send_extraction_complete(self, result: ExtractionResult, document_name: str = None):
        """
        Send extraction completion notification to Discord.
        
        Args:
            result: Extraction result
            document_name: Name of processed document
        """
        try:
            # Build rich embed
            embed = {
                "title": "✅ Financial Rules Extraction Complete",
                "color": 0x00ff00,  # Green
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "Document",
                        "value": document_name or result.document_id,
                        "inline": False
                    },
                    {
                        "name": "Rules Extracted",
                        "value": str(result.statistics.get('total_rules', 0)),
                        "inline": True
                    },
                    {
                        "name": "Gaps Found",
                        "value": str(result.statistics.get('total_gaps', 0)),
                        "inline": True
                    },
                    {
                        "name": "Processing Time",
                        "value": f"{result.processing_time_seconds:.2f}s",
                        "inline": True
                    }
                ]
            }
            
            # Add track breakdown
            rules_by_track = result.statistics.get('rules_by_track', {})
            if rules_by_track:
                track_text = "\n".join([
                    f"• {track}: {count}" 
                    for track, count in rules_by_track.items()
                    if count > 0
                ])
                embed["fields"].append({
                    "name": "Rules by Track",
                    "value": track_text,
                    "inline": False
                })
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Discord notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    def send_message(self, message: str, username: str = "Financial Rules Agent"):
        """
        Send a simple message to Discord.
        
        Args:
            message: Message text
            username: Bot username to display
        """
        try:
            payload = {
                "content": message,
                "username": username
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Discord message sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")


class EmailIntegration:
    """Email notification via SMTP."""
    
    def __init__(self, smtp_config: Dict):
        """
        Initialize Email integration.
        
        Args:
            smtp_config: SMTP configuration dictionary
        """
        self.config = smtp_config
    
    def send_extraction_complete(
        self, 
        result: ExtractionResult, 
        recipient: str,
        document_name: str = None
    ):
        """
        Send extraction completion notification via email.
        
        Args:
            result: Extraction result
            recipient: Email recipient
            document_name: Name of processed document
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'✅ Financial Rules Extraction Complete - {document_name or result.document_id}'
            msg['From'] = self.config.get('from')
            msg['To'] = recipient
            
            # Plain text version
            text_content = f"""
Financial Rules Extraction Complete

Document: {document_name or result.document_id}
Rules Extracted: {result.statistics.get('total_rules', 0)}
Gaps Found: {result.statistics.get('total_gaps', 0)}
Processing Time: {result.processing_time_seconds:.2f} seconds

Rules by Track:
"""
            rules_by_track = result.statistics.get('rules_by_track', {})
            for track, count in rules_by_track.items():
                if count > 0:
                    text_content += f"  • {track}: {count}\n"
            
            # HTML version
            html_content = f"""
<html>
<body>
    <h2>✅ Financial Rules Extraction Complete</h2>
    <p><strong>Document:</strong> {document_name or result.document_id}</p>
    <p><strong>Rules Extracted:</strong> {result.statistics.get('total_rules', 0)}</p>
    <p><strong>Gaps Found:</strong> {result.statistics.get('total_gaps', 0)}</p>
    <p><strong>Processing Time:</strong> {result.processing_time_seconds:.2f} seconds</p>
    
    <h3>Rules by Track:</h3>
    <ul>
"""
            for track, count in rules_by_track.items():
                if count > 0:
                    html_content += f"        <li>{track}: {count}</li>\n"
            
            html_content += """
    </ul>
</body>
</html>
"""
            
            # Attach parts
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.config.get('host'), self.config.get('port')) as server:
                server.starttls()
                server.login(self.config.get('user'), self.config.get('password'))
                server.send_message(msg)
            
            logger.info(f"Email notification sent successfully to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def send_email(self, recipient: str, subject: str, body: str, html: bool = False):
        """
        Send a generic email.
        
        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body
            html: Whether body is HTML
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(body, 'html' if html else 'plain')
            msg['Subject'] = subject
            msg['From'] = self.config.get('from')
            msg['To'] = recipient
            
            with smtplib.SMTP(self.config.get('host'), self.config.get('port')) as server:
                server.starttls()
                server.login(self.config.get('user'), self.config.get('password'))
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


class WebhookIntegration:
    """Generic webhook integration for custom endpoints."""
    
    def __init__(self, webhook_url: str, headers: Dict = None):
        """
        Initialize webhook integration.
        
        Args:
            webhook_url: Webhook URL
            headers: Custom headers to include
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    def send_extraction_complete(self, result: ExtractionResult, document_name: str = None):
        """
        Send extraction completion notification to webhook.
        
        Args:
            result: Extraction result
            document_name: Name of processed document
        """
        try:
            payload = {
                "event": "extraction_complete",
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": result.document_id,
                "document_name": document_name,
                "statistics": result.statistics,
                "processing_time_seconds": result.processing_time_seconds,
                "num_rules": len(result.extracted_rules),
                "num_gaps": len(result.gaps)
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Webhook notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    def send_webhook(self, payload: Dict, method: str = "POST"):
        """
        Send a generic webhook.
        
        Args:
            payload: Payload to send
            method: HTTP method (POST, PUT, etc.)
        """
        try:
            if method.upper() == "POST":
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            logger.info("Webhook sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")


class NotificationManager:
    """Manages all notification integrations."""
    
    def __init__(self):
        """Initialize notification manager with configured integrations."""
        self.slack = None
        self.discord = None
        self.email = None
        self.webhook = None
        
        # Initialize integrations based on configuration
        if config.integrations.enable_notifications:
            self._initialize_integrations()
    
    def _initialize_integrations(self):
        """Initialize enabled integrations."""
        # Slack
        if config.integrations.slack_webhook_url:
            try:
                self.slack = SlackIntegration(
                    webhook_url=config.integrations.slack_webhook_url,
                    channel=config.integrations.slack_channel
                )
                logger.info("Slack integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Slack integration: {e}")
        
        # Discord
        if config.integrations.discord_webhook_url:
            try:
                self.discord = DiscordIntegration(
                    webhook_url=config.integrations.discord_webhook_url
                )
                logger.info("Discord integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Discord integration: {e}")
        
        # Email
        if all([
            config.integrations.smtp_host,
            config.integrations.smtp_user,
            config.integrations.smtp_password,
            config.integrations.smtp_from
        ]):
            try:
                self.email = EmailIntegration({
                    'host': config.integrations.smtp_host,
                    'port': config.integrations.smtp_port,
                    'user': config.integrations.smtp_user,
                    'password': config.integrations.smtp_password,
                    'from': config.integrations.smtp_from
                })
                logger.info("Email integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Email integration: {e}")
        
        # Generic webhook
        if config.integrations.custom_webhook_url:
            try:
                self.webhook = WebhookIntegration(
                    webhook_url=config.integrations.custom_webhook_url
                )
                logger.info("Webhook integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Webhook integration: {e}")
    
    def notify_extraction_complete(
        self, 
        result: ExtractionResult, 
        document_name: str = None
    ):
        """
        Send extraction completion notification to all enabled channels.
        
        Args:
            result: Extraction result
            document_name: Name of processed document
        """
        if not config.integrations.enable_notifications:
            logger.debug("Notifications disabled")
            return
        
        logger.info("Sending notifications to enabled channels")
        
        # Slack
        if self.slack:
            try:
                self.slack.send_extraction_complete(result, document_name)
            except Exception as e:
                logger.warning(f"Slack notification failed: {e}")
        
        # Discord
        if self.discord:
            try:
                self.discord.send_extraction_complete(result, document_name)
            except Exception as e:
                logger.warning(f"Discord notification failed: {e}")
        
        # Email
        if self.email and config.integrations.notification_email:
            try:
                self.email.send_extraction_complete(
                    result,
                    config.integrations.notification_email,
                    document_name
                )
            except Exception as e:
                logger.warning(f"Email notification failed: {e}")
        
        # Generic webhook
        if self.webhook:
            try:
                self.webhook.send_extraction_complete(result, document_name)
            except Exception as e:
                logger.warning(f"Webhook notification failed: {e}")
    
    def is_configured(self) -> bool:
        """Check if any integrations are configured."""
        return any([self.slack, self.discord, self.email, self.webhook])
    
    def get_configured_channels(self) -> List[str]:
        """Get list of configured notification channels."""
        channels = []
        if self.slack:
            channels.append("Slack")
        if self.discord:
            channels.append("Discord")
        if self.email:
            channels.append("Email")
        if self.webhook:
            channels.append("Webhook")
        return channels
