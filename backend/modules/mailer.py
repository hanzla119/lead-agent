import asyncio
import random
import socket
import ssl
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from backend.config import (
    SENDER_NAME,
    SENDER_EMAIL,
    SMTP_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    RESEND_API_KEY,
    BREVO_API_KEY,
    SENDGRID_API_KEY,
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

def send_via_resend_http(to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
    """Sends email via Resend HTTP API over port 443 (Allowed by all cloud providers)."""
    try:
        sender_formatted = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        formatted_body = body_text.replace("\n", "<br>")
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": sender_formatted,
                "to": [to_email],
                "subject": subject,
                "html": f"<div style='font-family:sans-serif;font-size:15px;color:#2d3748;'>{formatted_body}</div>",
                "text": body_text
            },
            timeout=12
        )
        if resp.status_code in [200, 201]:
            return {"success": True, "message": f"Successfully delivered via Resend HTTP to {to_email}", "error": None}
        else:
            return {"success": False, "error": f"Resend API error ({resp.status_code}): {resp.text}"}
    except Exception as e:
        return {"success": False, "error": f"Resend HTTP error: {e}"}

def send_via_brevo_http(to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
    """Sends email via Brevo (Sendinblue) HTTP API over port 443."""
    try:
        formatted_body = body_text.replace("\n", "<br>")
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
            json={
                "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": f"<div style='font-family:sans-serif;font-size:15px;color:#2d3748;'>{formatted_body}</div>",
                "textContent": body_text
            },
            timeout=12
        )
        if resp.status_code in [200, 201]:
            return {"success": True, "message": f"Successfully delivered via Brevo HTTP to {to_email}", "error": None}
        else:
            return {"success": False, "error": f"Brevo API error ({resp.status_code}): {resp.text}"}
    except Exception as e:
        return {"success": False, "error": f"Brevo HTTP error: {e}"}

def get_ipv4_smtp_ssl(host: str = SMTP_HOST, port: int = 465, timeout: int = 15) -> smtplib.SMTP_SSL:
    """
    Forces IPv4 resolution and direct SSL encryption to bypass cloud container (Render/Docker)
    IPv6 routing failures ('[Errno 101] Network is unreachable').
    """
    addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    if not addr_info:
        raise ValueError(f"Could not resolve IPv4 address for {host}")
    
    sock = None
    last_err = None
    for family, socktype, proto, _, sockaddr in addr_info:
        try:
            s = socket.socket(family, socktype, proto)
            s.settimeout(timeout)
            s.connect(sockaddr)
            context = ssl.create_default_context()
            sock = context.wrap_socket(s, server_hostname=host)
            break
        except Exception as err:
            last_err = err
            if s:
                try:
                    s.close()
                except Exception:
                    pass
    
    if sock is None:
        raise last_err or Exception(f"Failed to connect to {host}:{port} via IPv4")
    
    server = smtplib.SMTP_SSL()
    server.sock = sock
    server.file = sock.makefile("rb")
    server.getreply()
    return server

def send_single_email_sync(to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
    """
    Universal email dispatcher supporting HTTP APIs (Resend, Brevo) and direct Gmail SMTP (SSL 465 / 587).
    """
    # 1. HTTP APIs (Bypasses Render/Cloud outbound port blocks over Port 443 HTTPS)
    if RESEND_API_KEY:
        return send_via_resend_http(to_email, subject, body_text)
    if BREVO_API_KEY:
        return send_via_brevo_http(to_email, subject, body_text)

    # 2. Direct Gmail SMTP via Forced IPv4 SSL on Port 465
    msg = create_email_message(to_email, subject, body_text)
    try:
        server = get_ipv4_smtp_ssl(SMTP_HOST, 465, timeout=12)
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return {"success": True, "message": f"Successfully delivered email to {to_email}", "error": None}
    except Exception as e465:
        # 3. Fallback to standard SMTP on Port 587
        try:
            server = smtplib.SMTP(SMTP_HOST, 587, timeout=10)
            server.starttls()
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return {"success": True, "message": f"Successfully delivered email to {to_email}", "error": None}
        except Exception as e587:
            error_msg = f"SMTP Connection Failed: {e465}. On Render free tier, outbound SMTP ports may be blocked. Add BREVO_API_KEY or RESEND_API_KEY in Render Environment to send via HTTPS Port 443."
            print(f"SMTP error to {to_email}: {error_msg}")
            return {"success": False, "error": error_msg}

async def send_single_email_async(to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
    """
    Asynchronous wrapper running forced IPv4 SSL in worker thread.
    """
    return await asyncio.to_thread(send_single_email_sync, to_email, subject, body_text)

def send_test_email_sync(to_email: str, subject: str, message: str) -> Dict[str, Any]:
    """
    Test email handler.
    """
    return send_single_email_sync(to_email, subject, message)

async def wait_rate_limit_delay(min_sec: int = MIN_DELAY_SECONDS, max_sec: int = MAX_DELAY_SECONDS):
    """
    Pauses execution with randomized jitter to simulate human sending cadence.
    """
    delay = random.randint(min_sec, max_sec)
    await asyncio.sleep(delay)
    return delay

