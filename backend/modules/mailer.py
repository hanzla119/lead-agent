import asyncio
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
import aiosmtplib

from backend.config import (
    SENDER_NAME,
    SENDER_EMAIL,
    SMTP_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS
)

def create_email_message(to_email: str, subject: str, body_text: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Reply-To"] = SENDER_EMAIL
    
    # Plain text version
    plain_text = f"{body_text}\n\n---\nIf you prefer not to hear from me, simply reply with 'unsubscribe' and I'll remove you immediately."
    part1 = MIMEText(plain_text, "plain", "utf-8")
    
    # HTML formatted version
    formatted_body = body_text.replace("\n", "<br>")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #2d3748;
                font-size: 15px;
                line-height: 1.6;
                padding: 10px;
            }}
            .content {{
                max-width: 600px;
                margin: 0 auto;
            }}
            .signature {{
                margin-top: 25px;
                padding-top: 15px;
                border-top: 1px solid #e2e8f0;
                color: #4a5568;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #a0aec0;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            <div>{formatted_body}</div>
            <div class="footer">
                <p>You received this email because of your public e-commerce brand presence.<br>
                If you would rather not receive marketing advice, please reply with "unsubscribe" to be permanently removed.</p>
            </div>
        </div>
    </body>
    </html>
    """
    part2 = MIMEText(html_content, "html", "utf-8")
    
    msg.attach(part1)
    msg.attach(part2)
    return msg

async def send_single_email_async(to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
    """
    Asynchronously dispatches a single email via Gmail SMTP with STARTTLS.
    """
    msg = create_email_message(to_email, subject, body_text)
    
    try:
        smtp_client = aiosmtplib.SMTP(
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            timeout=15
        )
        await smtp_client.connect()
        await smtp_client.login(SENDER_EMAIL, SMTP_PASSWORD)
        await smtp_client.send_message(msg)
        await smtp_client.quit()
        return {"success": True, "error": None}
    except Exception as e:
        error_msg = str(e)
        print(f"SMTP sending error to {to_email}: {error_msg}")
        return {"success": False, "error": error_msg}

def send_test_email_sync(to_email: str, subject: str, message: str) -> Dict[str, Any]:
    """
    Synchronous test sender to verify SMTP connection instantly.
    """
    msg = create_email_message(to_email, subject, message)
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12)
        server.starttls()
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return {"success": True, "message": f"Successfully delivered test email to {to_email}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def wait_rate_limit_delay(min_sec: int = MIN_DELAY_SECONDS, max_sec: int = MAX_DELAY_SECONDS):
    """
    Pauses execution with randomized jitter to simulate human sending cadence.
    """
    delay = random.randint(min_sec, max_sec)
    await asyncio.sleep(delay)
    return delay
