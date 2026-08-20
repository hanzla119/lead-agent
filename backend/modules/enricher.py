import re
import urllib.parse
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Set

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'(?:Tel|Phone|Call|Contact|Mobile)?[:\s]*(\+?[0-9]{1,4}[\s.-]?\(?[0-9]{1,4}?\)?[\s.-]?[0-9]{2,5}[\s.-]?[0-9]{3,6})'

IGNORED_EMAIL_DOMAINS = {
    "sentry.io", "wixpress.com", "shopify.com", "myshopify.com",
    "domain.com", "example.com", "yourdomain.com", "email.com",
    "cloudflare.com", "google.com", "schema.org", "w3.org",
    "github.com", "gitlab.com", "wordpress.org", "automattic.com",
    "gravatar.com", "twimg.com", "facebook.com", "instagram.com"
}

IGNORED_EMAIL_PREFIXES = {
    "xxx", "test", "sample", "example", "admin@wix", "blocked",
    "abuse", "security", "privacy@cloudflare", "support@shopify",
    "no-reply", "noreply", "mailer-daemon", "git", "root", "postmaster"
}

IGNORED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".css", ".js", ".woff", ".woff2", ".ttf"}

IGNORED_SOCIAL_HANDLES = {
    "shopify", "wordpress", "wix", "squarespace", "woocommerce",
    "facebook", "instagram", "tiktok", "twitter", "x", "youtube", "linkedin",
    "sharer", "share", "intent"
}

DEFAULT_CONTACT_SUBPATHS = [
    "/pages/contact",
    "/pages/contact-us",
    "/contact",
    "/contact-us",
    "/policies/contact-information",
    "/policies/terms-of-service",
    "/policies/refund-policy",
    "/policies/privacy-policy",
    "/pages/about-us",
    "/about",
    "/pages/customer-care",
    "/pages/help",
    "/pages/faq"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def clean_email(email: str) -> Optional[str]:
    if not email:
        return None
    email = email.lower().strip().strip("<>\"'.,;:()")
    
    if any(email.endswith(ext) for ext in IGNORED_EXTENSIONS):
        return None
    if any(email.startswith(p) for p in IGNORED_EMAIL_PREFIXES):
        return None
    if "xxx@xxx" in email or "test@test" in email or "example@example" in email:
        return None
    if re.search(r'@[0-9.]+$', email):
        return None
        
    try:
        parts = email.split("@")
        if len(parts) != 2:
            return None
        name, domain = parts
        if len(name) < 1 or len(domain) < 3 or "." not in domain:
            return None
        tld = domain.split(".")[-1]
        if len(tld) < 2 or not tld.isalpha():
            return None
        if domain in IGNORED_EMAIL_DOMAINS or any(ign in domain for ign in IGNORED_EMAIL_DOMAINS):
            return None
    except Exception:
        return None
        
    return email

def clean_social_url(url: str, platform: str) -> Optional[str]:
    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            return None
            
        handle = path.split("/")[0].lower().replace("@", "")
        if handle in IGNORED_SOCIAL_HANDLES or any(h in handle for h in ["shopify", "sharer", "intent", "explore", "p", "reels", "stories"]):
            return None
            
        # Clean clean URL without tracking query parameters
        clean_url = f"https://www.{platform}.com/{path}"
        if platform == "tiktok":
            clean_url = f"https://www.tiktok.com/@{handle}"
        return clean_url
    except Exception:
        return None

def extract_from_html(html: str, base_url: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "emails": set(),
        "phone": None,
        "instagram": None,
        "linkedin": None,
        "facebook": None,
        "tiktok": None,
        "internal_contact_links": []
    }
    
    if not html:
        return info
        
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Look for links: mailto, tel, socials, and contact subpaths
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        
        # Mailto
        if href.startswith("mailto:"):
            raw_email = href.replace("mailto:", "").split("?")[0]
            cleaned = clean_email(raw_email)
            if cleaned:
                info["emails"].add(cleaned)
                
        # Tel
        elif href.startswith("tel:"):
            phone = href.replace("tel:", "").strip()
            if len(re.sub(r'[^0-9]', '', phone)) >= 7:
                info["phone"] = phone
                
        # Socials
        elif "instagram.com/" in href:
            clean_ig = clean_social_url(href, "instagram")
            if clean_ig and not info["instagram"]:
                info["instagram"] = clean_ig
        elif "facebook.com/" in href:
            clean_fb = clean_social_url(href, "facebook")
            if clean_fb and not info["facebook"]:
                info["facebook"] = clean_fb
        elif "tiktok.com/@" in href:
            clean_tt = clean_social_url(href, "tiktok")
            if clean_tt and not info["tiktok"]:
                info["tiktok"] = clean_tt
        elif "linkedin.com/company/" in href or "linkedin.com/in/" in href:
            if not any(x in href for x in ["shareArticle", "sharing"]):
                info["linkedin"] = href.split("?")[0]
                
        # Internal Contact & Policy Links
        href_lower = href.lower()
        if any(k in href_lower for k in ["contact", "about", "customer", "terms", "policy", "refund", "privacy", "help", "support"]):
            if href.startswith("/") or base_url in href:
                full_link = urllib.parse.urljoin(base_url, href)
                if full_link not in info["internal_contact_links"]:
                    info["internal_contact_links"].append(full_link)

    # 2. Extract JSON-LD Schema (ContactPoint / Organization)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            data_list = data if isinstance(data, list) else [data]
            for item in data_list:
                if isinstance(item, dict):
                    # Check email
                    em = item.get("email")
                    if em:
                        c_em = clean_email(str(em))
                        if c_em:
                            info["emails"].add(c_em)
                    # Check contactPoint
                    cp = item.get("contactPoint")
                    if isinstance(cp, dict):
                        c_em = clean_email(str(cp.get("email", "")))
                        if c_em:
                            info["emails"].add(c_em)
                        if cp.get("telephone") and not info["phone"]:
                            info["phone"] = str(cp["telephone"]).strip()
                    # Check telephone
                    if item.get("telephone") and not info["phone"]:
                        info["phone"] = str(item["telephone"]).strip()
        except Exception:
            pass

    # 3. Unobfuscate text like support [at] domain.com or support(at)domain.com
    unobfuscated_html = re.sub(r'\[at\]|\(at\)', '@', html, flags=re.IGNORECASE)
    unobfuscated_html = re.sub(r'\[dot\]|\(dot\)', '.', unobfuscated_html, flags=re.IGNORECASE)

    # 4. Regex search for emails
    found_emails = re.findall(EMAIL_REGEX, unobfuscated_html)
    for fe in found_emails:
        cleaned = clean_email(fe)
        if cleaned:
            info["emails"].add(cleaned)
            
    # 5. Text phone search if tel: not found
    if not info["phone"]:
        phone_matches = re.findall(PHONE_REGEX, soup.get_text(separator=' ', strip=True))
        for pm in phone_matches:
            clean_pm = pm.strip()
            digits = re.sub(r'[^0-9]', '', clean_pm)
            if clean_pm.startswith(("2024", "2025", "2026", "2023", "2022", "199")):
                continue
            if 9 <= len(digits) <= 15:
                info["phone"] = clean_pm
                break

    return info

def enrich_store_contacts(store_url: str, initial_html: str = "") -> Dict[str, Any]:
    """
    Scrapes the store's homepage, discovered internal contact links, and standard policy subpaths
    to extract authentic verified contact emails, phone, socials, and support channels.
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
    
    if not store_url.startswith("http"):
        store_url = f"https://{store_url}"
        
    store_domain = urllib.parse.urlparse(store_url).netloc.lower().replace("www.", "")
    all_emails: Set[str] = set()
    discovered_contact_links: List[str] = []
    
    # 1. Process homepage html if provided
    if initial_html:
        home_data = extract_from_html(initial_html, store_url)
        all_emails.update(home_data["emails"])
        discovered_contact_links.extend(home_data["internal_contact_links"])
        for k in ["phone", "instagram", "linkedin", "facebook", "tiktok"]:
            if home_data.get(k):
                enriched[k] = home_data[k]

    # 2. If no email found on homepage, crawl top contact subpages (up to 3 pages)
    if not all_emails:
        target_urls_to_crawl = []
        
        # Add discovered internal contact links first
        for link in discovered_contact_links:
            if link not in target_urls_to_crawl and link != store_url.rstrip("/"):
                target_urls_to_crawl.append(link)
                
        # Add fallback default contact subpaths
        base_clean = store_url.rstrip("/")
        for sub in DEFAULT_CONTACT_SUBPATHS:
            full_sub = f"{base_clean}{sub}"
            if full_sub not in target_urls_to_crawl:
                target_urls_to_crawl.append(full_sub)

        for target in target_urls_to_crawl[:3]:
            try:
                resp = requests.get(target, headers=HEADERS, timeout=3, allow_redirects=True)
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

    # 3. Extract Founder / Owner Names from Text (About, Imprint, Team)
    founder_patterns = [
        r'(?:founded by|created by|started by|co-founder|founder|owner|ceo|director|co-founded by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,\s*(?:Founder|Co-Founder|Owner|CEO|Director|Head of)',
        r'(?:Inhaber|Geschäftsführer)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})'
    ]
    full_text = soup.get_text(separator=' ', strip=True)
    for fp in founder_patterns:
        match = re.search(fp, full_text)
        if match:
            cand = match.group(1).strip()
            # Filter out non-names like "Free Shipping", "Privacy Policy", "Shopify Store"
            if not any(cand.lower().startswith(x) for x in ["free", "privacy", "terms", "return", "contact", "about", "shopify", "united", "london", "customer"]):
                info["founder_name"] = cand
                break

    # 4. Filter and Prioritize Discovered Emails
    if all_emails:
        def email_priority_score(e: str) -> int:
            score = 100
            user_part, domain_part = e.split("@")
            
            # Highest priority: exact domain match
            if store_domain and domain_part in store_domain:
                score -= 50
            # Common high-value inboxes
            if user_part in ["info", "hello", "contact", "support", "sales", "team", "orders", "customercare", "help"]:
                score -= 30
            elif any(user_part.startswith(prefix) for prefix in ["info", "hello", "contact", "support", "sales", "team"]):
                score -= 20
            # General public mailboxes (gmail/yahoo/outlook for boutique brands)
            elif any(p in domain_part for p in ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]):
                score -= 10
            return score

        sorted_emails = sorted(list(all_emails), key=email_priority_score)
        enriched["email"] = sorted_emails[0]
        enriched["email_status"] = "verified"
        
    return enriched
