"""通知技能实现

支持多通道通知发送：控制台、邮件、短信、Webhook。
邮件和短信通道使用环境变量配置，未配置时优雅降级。
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

LEVEL_COLORS = {
    "info": "#2196F3",
    "warning": "#FF9800",
    "error": "#F44336",
    "success": "#4CAF50",
}


def _build_html_email(message: str, level: str, title: str = "lingflow 通知") -> str:
    color = LEVEL_COLORS.get(level, "#2196F3")
    return f"""<!DOCTYPE html>
<html><body style="font-family: sans-serif; margin: 0; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
  <div style="background: {color}; color: white; padding: 16px 24px;">
    <h2 style="margin: 0;">{title}</h2>
  </div>
  <div style="padding: 24px;">
    <p style="font-size: 16px; line-height: 1.6;">{message}</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 16px 0;">
    <p style="font-size: 12px; color: #999;">级别: {level.upper()}</p>
  </div>
</div>
</body></html>"""


def send_email(
    message: str,
    level: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to_address: str,
    subject: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = smtp_user
        msg["To"] = to_address
        msg["Subject"] = subject or f"[lingflow] {level.upper()} 通知"

        msg.attach(MIMEText(message, "plain", "utf-8"))
        msg.attach(MIMEText(_build_html_email(message, level), "html", "utf-8"))

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.starttls()

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_address], msg.as_string())
        server.quit()

        return {
            "success": True,
            "channel": "email",
            "level": level,
            "status": "sent",
            "recipient": to_address,
        }
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return {
            "success": False,
            "channel": "email",
            "level": level,
            "status": "failed",
            "error": str(e),
        }


def send_sms_via_webhook(
    message: str,
    level: str,
    webhook_url: str,
    phone: str,
) -> Dict[str, Any]:
    try:
        import requests

        payload = {
            "phone": phone,
            "message": f"[{level.upper()}] {message}",
            "level": level,
        }
        resp = requests.post(webhook_url, json=payload, timeout=15)

        if resp.status_code == 200:
            return {
                "success": True,
                "channel": "sms",
                "level": level,
                "status": "sent",
                "phone": phone,
            }
        return {
            "success": False,
            "channel": "sms",
            "level": level,
            "status": "failed",
            "error": f"HTTP {resp.status_code}",
        }
    except Exception as e:
        logger.error("SMS webhook failed: %s", e)
        return {
            "success": False,
            "channel": "sms",
            "level": level,
            "status": "failed",
            "error": str(e),
        }


def send_webhook(
    message: str,
    level: str,
    webhook_url: str,
) -> Dict[str, Any]:
    try:
        import requests

        payload = {"message": message, "level": level, "source": "lingflow"}
        resp = requests.post(webhook_url, json=payload, timeout=15)

        if resp.status_code == 200:
            return {
                "success": True,
                "channel": "webhook",
                "level": level,
                "status": "sent",
            }
        return {
            "success": False,
            "channel": "webhook",
            "level": level,
            "status": "failed",
            "error": f"HTTP {resp.status_code}",
        }
    except Exception as e:
        logger.error("Webhook notification failed: %s", e)
        return {
            "success": False,
            "channel": "webhook",
            "level": level,
            "status": "failed",
            "error": str(e),
        }


def send_console_notification(message: str, level: str) -> Dict[str, Any]:
    prefix_map = {"info": "[INFO]", "warning": "[WARNING]", "error": "[ERROR]", "success": "[OK]"}
    prefix = prefix_map.get(level, "[INFO]")
    print(f"{prefix} {message}")
    return {
        "success": True,
        "channel": "console",
        "level": level,
        "status": "sent",
    }


def send_notification(params: Dict[str, Any]) -> Dict[str, Any]:
    message = params.get("message", "")
    level = params.get("level", "info")
    channel = params.get("channel", "console")

    if not message:
        return {"error": "请指定通知消息", "success": False}

    if channel == "console":
        return send_console_notification(message, level)

    elif channel == "email":
        import os

        smtp_host = os.environ.get("LINGFLOW_SMTP_HOST")
        smtp_port_str = os.environ.get("LINGFLOW_SMTP_PORT", "587")
        try:
            smtp_port = int(smtp_port_str)
        except ValueError:
            smtp_port = 587
        smtp_user = os.environ.get("LINGFLOW_SMTP_USER", "")
        smtp_password = os.environ.get("LINGFLOW_SMTP_PASSWORD", "")
        to_address = params.get("to") or os.environ.get("LINGFLOW_NOTIFY_EMAIL", "")

        if not all([smtp_host, smtp_user, smtp_password, to_address]):
            return {
                "success": False,
                "channel": "email",
                "status": "skipped",
                "reason": "SMTP not configured. Set LINGFLOW_SMTP_HOST/USER/PASSWORD and LINGFLOW_NOTIFY_EMAIL.",
            }
        return send_email(
            message, level, smtp_host, smtp_port, smtp_user, smtp_password, to_address,
            subject=params.get("subject"),
        )

    elif channel == "sms":
        import os

        webhook_url = os.environ.get("LINGFLOW_SMS_WEBHOOK", "")
        phone = params.get("phone") or os.environ.get("LINGFLOW_SMS_PHONE", "")

        if not all([webhook_url, phone]):
            return {
                "success": False,
                "channel": "sms",
                "status": "skipped",
                "reason": "SMS not configured. Set LINGFLOW_SMS_WEBHOOK and LINGFLOW_SMS_PHONE.",
            }
        return send_sms_via_webhook(message, level, webhook_url, phone)

    elif channel == "webhook":
        webhook_url = params.get("webhook_url", "")
        if not webhook_url:
            return {
                "success": False,
                "channel": "webhook",
                "status": "skipped",
                "reason": "webhook_url parameter required.",
            }
        return send_webhook(message, level, webhook_url)

    else:
        return send_console_notification(message, level)


def execute_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    return send_notification(params)
