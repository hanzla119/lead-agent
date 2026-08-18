import os
from dotenv import load_dotenv

load_dotenv()

# Sender Configuration
SENDER_NAME = os.getenv("SENDER_NAME", "Talha Yousaf")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "marketingbytalha@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

# Cloud HTTP Email Fallbacks (Bypasses Render/Cloud free tier SMTP port blocks)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

# AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Outreach Safety & Limits
MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "25"))
MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "45"))
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "100"))

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "leads_data.db")
