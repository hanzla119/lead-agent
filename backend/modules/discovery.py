import re
import urllib.parse
from typing import List, Dict, Any

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# Aggregator, marketplace, directory domains to exclude
EXCLUDED_DOMAINS = {
    "amazon.com", "amazon.co.uk", "ebay.com", "ebay.co.uk", "aliexpress.com",
    "etsy.com", "walmart.com", "target.com", "pinterest.com", "youtube.com",
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "wikipedia.org", "medium.com", "quora.com", "reddit.com", "trustpilot.com",
    "yellowpages.com", "yelp.com", "shopify.com", "myshopify.com", "asos.com",
    "shein.com", "temu.com", "tiktok.com", "bloomberg.com", "forbes.com",
    "github.com", "gitlab.com", "tripadvisor.com", "booking.com"
}

def extract_domain(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        netloc = netloc.split(":")[0]
        return netloc
    except Exception:
        return ""

def clean_store_name(title: str, domain: str) -> str:
    cleaned = re.split(r"[-–|:—•]", title)[0].strip()
    cleaned = re.sub(r'(?i)(official site|online store|uk store|shop online|official store|home|boutique)', '', cleaned).strip()
    if not cleaned or len(cleaned) > 35 or len(cleaned) < 2:
        base = domain.split(".")[0]
        cleaned = base.replace("-", " ").replace("_", " ").title()
    return cleaned

def build_search_queries(niche: str, platform: str, country: str) -> List[str]:
    queries = []
    country_hint = "UK" if country.upper() == "UK" else country

    if platform.lower() == "shopify":
        queries.append(f"{niche} brand shopify {country_hint}")
        queries.append(f"{niche} clothing online store {country_hint}")
        queries.append(f"{niche} independent brands shopify")
        queries.append(f"{niche} store collections products")
        queries.append(f"best {niche} shopify stores {country_hint}")
        queries.append(f"{niche} boutique online shop {country_hint}")
    elif platform.lower() == "woocommerce":
        queries.append(f"{niche} woocommerce store {country_hint}")
        queries.append(f"{niche} online store wordpress {country_hint}")
    elif platform.lower() == "instagram":
        queries.append(f"{niche} brand shop instagram {country_hint}")
        queries.append(f"{niche} store link in bio")
    else:
        queries.append(f"{niche} brand online store {country_hint}")
        queries.append(f"{niche} independent boutique {country_hint}")

    return queries

def discover_leads(niche: str, platform: str = "Shopify", country: str = "UK", limit: int = 10) -> List[Dict[str, Any]]:
    discovered: Dict[str, Dict[str, Any]] = {}
    queries = build_search_queries(niche, platform, country)
    needed = max(limit, 10)
    
    try:
        with DDGS() as ddgs:
            for q in queries:
                if len(discovered) >= needed:
                    break
                try:
                    results = list(ddgs.text(q, max_results=25))
                    for res in results:
                        url = res.get("href") or res.get("url", "")
                        title = res.get("title", "")
                        snippet = res.get("body", "")
                        
                        if not url or not url.startswith("http"):
                            continue
                            
                        domain = extract_domain(url)
                        if not domain or domain in EXCLUDED_DOMAINS:
                            continue
                        if any(domain.endswith("." + ex) or ex in domain for ex in EXCLUDED_DOMAINS):
                            continue
                        
                        if domain in discovered:
                            continue
                        
                        store_name = clean_store_name(title, domain)
                        target_url = f"https://{domain}"
                        
                        discovered[domain] = {
                            "domain": domain,
                            "store_name": store_name,
                            "url": target_url,
                            "niche": niche,
                            "platform": platform,
                            "country": country,
                            "title": title,
                            "snippet": snippet
                        }
                        
                        if len(discovered) >= needed:
                            break
                except Exception as e:
                    print(f"Error querying '{q}': {e}")
                    continue
    except Exception as outer_e:
        print(f"DDGS outer initialization error: {outer_e}")

    return list(discovered.values())[:limit]
