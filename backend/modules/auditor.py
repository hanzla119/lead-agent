import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Tuple

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

NON_STORE_KEYWORDS = [
    "attention required! | cloudflare",
    "just a moment...",
    "error page",
    "access denied",
    "403 forbidden",
    "404 not found",
    "domain for sale",
    "buy this domain",
    "web development agency",
    "shopify agency",
    "ecommerce agency",
    "marketing agency",
    "we are a digital agency",
    "read blog post",
    "posted on",
    "published on",
    "leave a comment",
    "best shopify stores in",
    "top shopify stores",
    "affiliate disclosure"
]

ECOMMERCE_SIGNALS = [
    "add to cart", "add to bag", "add to basket", "buy now", "checkout",
    "cart", "bag", "basket", "products", "collections", "free shipping",
    "free delivery", "currency", "price", "schema.org/product", "schema.org/offer",
    "shopify", "woocommerce", "bigcommerce", "klaviyo", "shop pay", "apple pay"
]

def audit_website(url: str, timeout: int = 8) -> Tuple[Dict[str, Any], str]:
    """
    Audits a live store URL for e-commerce validity, Meta Pixel, GA4, TikTok Pixel,
    Google Ads, Klaviyo, Reviews, platform stack, and CRO opportunities.
    Returns audit dictionary and raw html content for further enrichment.
    """
    result: Dict[str, Any] = {
        "is_live": False,
        "is_valid_store": False,
        "rejection_reason": "",
        "platform": "Unknown",
        "final_url": url,
        "has_meta_pixel": False,
        "has_ga4": False,
        "has_tiktok_pixel": False,
        "has_google_ads": False,
        "has_klaviyo": False,
        "has_reviews": False,
        "audit_notes": "",
        "primary_opportunity": ""
    }
    
    if not url.startswith("http"):
        url = f"https://{url}"
        
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        result["final_url"] = str(resp.url)
        
        if resp.status_code >= 400:
            result["rejection_reason"] = f"HTTP {resp.status_code}"
            result["audit_notes"] = f"Website returned HTTP status code {resp.status_code}"
            return result, ""
            
        html = resp.text
        html_lower = html.lower()
        result["is_live"] = True
        
        # 1. Check for Cloudflare captcha / Block pages / Domain parkers
        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
        title_lower = page_title.lower()
        
        if any(b in title_lower or b in html_lower[:1500] for b in [
            "attention required! | cloudflare", "just a moment...", "403 forbidden",
            "access denied", "blocked", "error page"
        ]):
            result["is_valid_store"] = False
            result["rejection_reason"] = f"Blocked/Cloudflare page ({page_title or 'Challenge'})"
            result["audit_notes"] = "Website returned a security block or challenge page"
            return result, ""
            
        # 2. Check for Marketing Agencies / SaaS / Tech blog listicles
        if any(b in title_lower for b in ["agency", "consulting", "marketing services", "web design agency", "best shopify stores", "top 100 shopify"]):
            result["is_valid_store"] = False
            result["rejection_reason"] = f"Agency/Blog Listicle ({page_title})"
            result["audit_notes"] = "Identified as agency or blog listicle, not an active storefront"
            return result, ""

        # 3. Platform Detection
        if "cdn.shopify.com" in html or "Shopify.theme" in html or "myshopify.com" in html or "window.Shopify" in html:
            result["platform"] = "Shopify"
        elif "wp-content/plugins/woocommerce" in html or "woocommerce-page" in html or "woocommerce" in html_lower:
            result["platform"] = "WooCommerce"
        elif "bigcommerce" in html_lower:
            result["platform"] = "BigCommerce"
        elif "magento" in html_lower or "Mage.Cookies" in html:
            result["platform"] = "Magento"
        elif "squarespace" in html_lower:
            result["platform"] = "Squarespace"
        elif "wix.com" in html_lower:
            result["platform"] = "Wix Store"
        elif "prestashop" in html_lower:
            result["platform"] = "PrestaShop"
        else:
            result["platform"] = "Custom / Headless"

        # 4. E-commerce Validity Verification
        ecommerce_matches = sum(1 for sig in ECOMMERCE_SIGNALS if sig in html_lower)
        has_cart = bool(re.search(r'\b(cart|basket|bag|checkout|shop)\b', html_lower))
        has_products = bool("/products/" in html or "/collections/" in html or "/product/" in html or "schema.org/product" in html_lower)
        
        # Site is accepted as a valid store if it has platform footprint or strong commerce signals
        if result["platform"] in ["Shopify", "WooCommerce", "BigCommerce", "Magento", "PrestaShop"] or (ecommerce_matches >= 3 and (has_cart or has_products)):
            result["is_valid_store"] = True
        else:
            # Check if it has prices or buy buttons
            if re.search(r'[£$€₹]\s*[0-9]+|\badd to cart\b|\bbuy now\b', html_lower):
                result["is_valid_store"] = True
            else:
                result["is_valid_store"] = False
                result["rejection_reason"] = "Non-ecommerce or informational page"
                result["audit_notes"] = "Page lacks shopping cart, product catalog, or checkout infrastructure"
                return result, html

        # 5. Meta / Facebook Pixel Detection
        meta_patterns = [
            r"fbq\(",
            r"connect\.facebook\.net\/[a-zA-Z_]+\/fbevents\.js",
            r"facebook-pixel",
            r"_fbq\b",
            r"_fbp\b"
        ]
        result["has_meta_pixel"] = any(re.search(p, html, re.IGNORECASE) for p in meta_patterns)

        # 6. TikTok Pixel Detection
        tt_patterns = [
            r"ttq\.load\(",
            r"analytics\.tiktok\.com",
            r"tiktok-pixel",
            r"ttq\.page\("
        ]
        result["has_tiktok_pixel"] = any(re.search(p, html, re.IGNORECASE) for p in tt_patterns)

        # 7. Google Analytics 4 / GTM / Google Ads Detection
        ga_patterns = [
            r"gtag\(['\"]config['\"],\s*['\"]G-",
            r"googletagmanager\.com\/gtm\.js",
            r"googletagmanager\.com\/gtag\/js\?id=G-",
            r"dataLayer\s*=\s*\["
        ]
        result["has_ga4"] = any(re.search(p, html, re.IGNORECASE) for p in ga_patterns)

        gads_patterns = [
            r"gtag\(['\"]config['\"],\s*['\"]AW-",
            r"google_conversion_id",
            r"googleadservices\.com\/pagead\/conversion",
            r"googleads\.g\.doubleclick\.net",
            r"google-shopping",
            r"google_tag_params"
        ]
        result["has_google_ads"] = any(re.search(p, html, re.IGNORECASE) for p in gads_patterns)

        # 8. Klaviyo / Email Marketing Detection
        klaviyo_patterns = [
            r"static\.klaviyo\.com",
            r"klaviyo\.js",
            r"_learnq\b"
        ]
        result["has_klaviyo"] = any(re.search(p, html, re.IGNORECASE) for p in klaviyo_patterns)

        # 9. Review Widgets Detection (Judge.me, Loox, Yotpo, Stamped, Trustpilot)
        review_patterns = [
            r"judge\.me",
            r"loox\.io",
            r"yotpo\.com",
            r"stamped\.io",
            r"trustpilot\.com\/reviews"
        ]
        result["has_reviews"] = any(re.search(p, html, re.IGNORECASE) for p in review_patterns)

        # 10. Lead Score (0-100) & Estimated Revenue Tier
        score = 40  # Base for active live store
        if result["platform"] in ["Shopify", "WooCommerce"]:
            score += 15
        if has_products or has_cart:
            score += 10
        if result["has_reviews"]:
            score += 10
            
        # Value opportunities add to outreach score
        if not result["has_google_ads"]:
            score += 15  # Prime candidate for $10k->$30k 45-day Google Ads scale
        if not result["has_meta_pixel"]:
            score += 10  # Immediate pixel leak fix
            
        result["lead_score"] = min(100, max(20, score))
        
        if result["lead_score"] >= 80:
            result["lead_tier"] = "Platinum"
            result["est_monthly_revenue"] = "$50k-$250k"
        elif result["lead_score"] >= 65:
            result["lead_tier"] = "Gold"
            result["est_monthly_revenue"] = "$10k-$50k"
        elif result["lead_score"] >= 45:
            result["lead_tier"] = "Silver"
            result["est_monthly_revenue"] = "$10k-$50k"
        else:
            result["lead_tier"] = "Bronze"
            result["est_monthly_revenue"] = "<$10k"

        # 11. Formulate Primary Opportunity Hook (Prioritizing Google Ads 45-day Scale Guarantee)
        gaps = []
        if not result["has_google_ads"]:
            gaps.append("Missing Google Ads & Shopping capture (leaking high-intent search buyers to competitors)")
            result["primary_opportunity"] = "Missing Google Shopping/Search Ads - Prime candidate for $10k->$30k/mo in 45 days (0.5-2x ROAS boost guaranteed)"
        elif not result["has_meta_pixel"]:
            gaps.append("Missing Meta/Facebook Pixel tracking (losing 30-40% retargeting buyers & CAPI attribution)")
            result["primary_opportunity"] = "Missing Meta Pixel Leak - Losing retargeting buyers; scale to $30k/mo via Google & Meta Ads"
        elif not result["has_tiktok_pixel"]:
            gaps.append("Missing TikTok Pixel (untapped high-converting Gen-Z impulse buyer demographic)")
            result["primary_opportunity"] = "Missing TikTok Ads tracking - untapped mobile scale opportunity alongside Google Ads"
        elif not result["has_ga4"]:
            gaps.append("Missing standard GA4 / GTM event tracking for purchase attribution")
            result["primary_opportunity"] = "Incomplete GA4 tracking & purchase attribution gaps - fix & scale to $30k/mo"
        elif not result["has_klaviyo"]:
            gaps.append("Missing Klaviyo abandoned cart automated flows and post-purchase winback sequences")
            result["primary_opportunity"] = "Uncaptured cart abandonment revenue (missing automated Klaviyo flows)"
        else:
            gaps.append("Full tracking detected; primary opportunity is scaling Google Performance Max & ROAS with guaranteed 0.5-2x lift")
            result["primary_opportunity"] = "Scale Shopify from $10k to $30k/mo in 45 days via Google Shopping & PMax (0.5-2x ROAS lift guaranteed)"

        result["audit_notes"] = "; ".join(gaps)
        return result, html

    except requests.exceptions.RequestException as e:
        result["is_live"] = False
        result["lead_score"] = 20
        result["lead_tier"] = "Bronze"
        result["est_monthly_revenue"] = "<$10k"
        result["rejection_reason"] = f"Failed to connect: {str(e)[:40]}"
        result["audit_notes"] = f"Failed to connect: {str(e)[:60]}"
        return result, ""
