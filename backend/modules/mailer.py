import asyncio
import random
import socket
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

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
    Synchronous email dispatcher using forced IPv4 SSL with STARTTLS fallback.
    """
    msg = create_email_message(to_email, subject, body_text)
    
    # 1. Primary: Forced IPv4 SSL on Port 465 (100% reliable on Render/Cloud hosts)
    try:
        server = get_ipv4_smtp_ssl(SMTP_HOST, 465, timeout=15)
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return {"success": True, "message": f"Successfully delivered email to {to_email}", "error": None}
    except Exception as e465:
        # 2. Secondary: Fallback to standard SMTP on Port 587
        try:
            server = smtplib.SMTP(SMTP_HOST, 587, timeout=12)
            server.starttls()
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return {"success": True, "message": f"Successfully delivered email to {to_email}", "error": None}
        except Exception as e587:
            error_msg = str(e465)
            print(f"SMTP error to {to_email}: SSL(465): {e465} | STARTTLS(587): {e587}")
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

