import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Tuple

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def audit_website(url: str, timeout: int = 8) -> Tuple[Dict[str, Any], str]:
    """
    Audits a live store URL for Meta Pixel, GA4, TikTok Pixel, platform stack, and CRO opportunities.
    Returns audit dictionary and raw html content for further enrichment.
    """
    result = {
        "is_live": False,
        "platform": "Unknown",
        "has_meta_pixel": False,
        "has_ga4": False,
        "has_tiktok_pixel": False,
        "audit_notes": "",
        "primary_opportunity": ""
    }
    
    if not url.startswith("http"):
        url = f"https://{url}"
        
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            result["audit_notes"] = f"HTTP status code {resp.status_code}"
            return result, ""
            
        html = resp.text
        result["is_live"] = True
        
        # 1. Platform Detection
        if "cdn.shopify.com" in html or "Shopify.theme" in html or "myshopify.com" in html:
            result["platform"] = "Shopify"
        elif "wp-content/plugins/woocommerce" in html or "woocommerce-page" in html:
            result["platform"] = "WooCommerce"
        elif "bigcommerce" in html:
            result["platform"] = "BigCommerce"
        elif "magento" in html or "Mage.Cookies" in html:
            result["platform"] = "Magento"
        else:
            result["platform"] = "Custom / Headless"

        # 2. Meta / Facebook Pixel Detection
        meta_patterns = [
            r"fbq\(",
            r"connect\.facebook\.net\/[a-zA-Z_]+\/fbevents\.js",
            r"facebook-pixel",
            r"_fbq\b"
        ]
        result["has_meta_pixel"] = any(re.search(p, html, re.IGNORECASE) for p in meta_patterns)

        # 3. Google Analytics 4 / GTM Detection
        ga_patterns = [
            r"gtag\(",
            r"googletagmanager\.com\/gtm\.js",
            r"googletagmanager\.com\/gtag\/js",
            r"G-[A-Z0-9]{6,12}",
            r"dataLayer\s*=\s*\["
        ]
        result["has_ga4"] = any(re.search(p, html, re.IGNORECASE) for p in ga_patterns)

        # 4. TikTok Pixel Detection
        tt_patterns = [
            r"ttq\.load\(",
            r"analytics\.tiktok\.com",
            r"tiktok-pixel"
        ]
        result["has_tiktok_pixel"] = any(re.search(p, html, re.IGNORECASE) for p in tt_patterns)

        # 5. Determine Primary Opportunity Hook
        gaps = []
        if not result["has_meta_pixel"]:
            gaps.append("Missing Meta/Facebook Pixel tracking (losing retargeting buyers & iOS 14+ conversion tracking)")
            result["primary_opportunity"] = "Missing Meta Pixel - losing 30-40% potential retargeting revenue"
        elif not result["has_tiktok_pixel"]:
            gaps.append("Missing TikTok Pixel (untapped high-converting Gen-Z / impulse buyer demographic)")
            result["primary_opportunity"] = "Missing TikTok Ads tracking - untapped scale opportunity"
        elif not result["has_ga4"]:
            gaps.append("Missing standard GA4 / GTM event tracking for purchase attribution")
            result["primary_opportunity"] = "Incomplete GA4 tracking & attribution gaps"
        else:
            gaps.append("Full tracking detected; opportunity lies in scaling ROAS, CRO landing page optimization, and creative ad testing")
            result["primary_opportunity"] = "Ad creative scaling & conversion rate optimization (CRO)"

        result["audit_notes"] = "; ".join(gaps)
        return result, html

    except requests.exceptions.RequestException as e:
        result["audit_notes"] = f"Failed to connect: {str(e)[:60]}"
        return result, ""
