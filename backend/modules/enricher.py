import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'(\+?[0-9]{1,4}?[-.\s]?\(?[0-9]{1,4}?\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9})'

IGNORED_EMAIL_DOMAINS = {
    "sentry.io", "wixpress.com", "shopify.com", "myshopify.com",
    "domain.com", "example.com", "yourdomain.com", "email.com",
    "cloudflare.com", "google.com", "schema.org"
}

IGNORED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".css", ".js"}

CONTACT_SUBPATHS = [
    "/pages/contact",
    "/pages/contact-us",
    "/contact",
    "/contact-us",
    "/about",
    "/pages/about-us",
    "/policies/privacy-policy",
    "/policies/terms-of-service"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def clean_email(email: str) -> Optional[str]:
    email = email.lower().strip()
    if any(email.endswith(ext) for ext in IGNORED_EXTENSIONS):
        return None
    # Filter out npm package patterns like name@1.2.3
    if re.search(r'@[0-9.]+$', email):
        return None
    try:
        parts = email.split("@")
        if len(parts) != 2:
            return None
        name, domain = parts
        if "." not in domain:
            return None
        tld = domain.split(".")[-1]
        if len(tld) < 2 or not tld.isalpha():
            return None
        if domain in IGNORED_EMAIL_DOMAINS or any(ign in domain for ign in IGNORED_EMAIL_DOMAINS):
            return None
    except Exception:
        return None
    return email

def extract_from_html(html: str, base_url: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "emails": set(),
        "phone": None,
        "instagram": None,
        "linkedin": None,
        "facebook": None,
        "tiktok": None
    }
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Look for mailto: links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("mailto:"):
            raw_email = href.replace("mailto:", "").split("?")[0]
            cleaned = clean_email(raw_email)
            if cleaned:
                info["emails"].add(cleaned)
        elif "instagram.com/" in href and not any(x in href for x in ["instagram.com/p/", "instagram.com/explore/"]):
            info["instagram"] = href
        elif "linkedin.com/company/" in href or "linkedin.com/in/" in href:
            info["linkedin"] = href
        elif "facebook.com/" in href and not any(x in href for x in ["sharer", "share"]):
            info["facebook"] = href
        elif "tiktok.com/@" in href:
            info["tiktok"] = href
        elif href.startswith("tel:"):
            info["phone"] = href.replace("tel:", "").strip()

    # 2. Text regex search for emails
    found_emails = re.findall(EMAIL_REGEX, html)
    for fe in found_emails:
        cleaned = clean_email(fe)
        if cleaned:
            info["emails"].add(cleaned)
            
    return info

def enrich_store_contacts(store_url: str, initial_html: str = "") -> Dict[str, Any]:
    """
    Scrapes the store's homepage and priority contact subpages to locate email, phone, and socials.
    """
    enriched: Dict[str, Any] = {
        "email": None,
        "email_status": "not_found",
        "phone": None,
        "instagram": None,
        "linkedin": None,
        "facebook": None,
        "tiktok": None,
        "founder_name": None
    }
    
    all_emails = set()
    
    # Process homepage html if provided
    if initial_html:
        home_data = extract_from_html(initial_html, store_url)
        all_emails.update(home_data["emails"])
        for k in ["phone", "instagram", "linkedin", "facebook", "tiktok"]:
            if home_data.get(k):
                enriched[k] = home_data[k]

    # If no email found on homepage, crawl contact subpages
    if not all_emails:
        base_clean = store_url.rstrip("/")
        for subpath in CONTACT_SUBPATHS[:3]: # check top 3 subpaths
            try:
                target = f"{base_clean}{subpath}"
                resp = requests.get(target, headers=HEADERS, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    sub_data = extract_from_html(resp.text, base_clean)
                    all_emails.update(sub_data["emails"])
                    for k in ["phone", "instagram", "linkedin", "facebook", "tiktok"]:
                        if not enriched.get(k) and sub_data.get(k):
                            enriched[k] = sub_data[k]
                    if all_emails:
                        break
            except Exception:
                continue

    if all_emails:
        # Prioritize info@, contact@, support@, hello@, sales@
        sorted_emails = sorted(
            list(all_emails),
            key=lambda e: (
                0 if e.startswith(("info@", "contact@", "hello@", "support@", "sales@")) else 1
            )
        )
        enriched["email"] = sorted_emails[0]
        enriched["email_status"] = "verified"
        
    return enriched
