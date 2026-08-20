import json
from typing import List, Dict, Any, Tuple
from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

def generate_pitches_with_gemini(lead_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Calls Google Gemini AI to craft:
    1. 5 distinct cold email pitch variants (featuring the Flagship 45-Day $10k->$30k Google Ads scale offer).
    2. Multi-channel copies for LinkedIn, Instagram DM, Reddit DM, and a 30-sec Loom video script.
    """
    store_name = lead_data.get("store_name", "your store")
    domain = lead_data.get("domain", "")
    founder_name = lead_data.get("founder_name") or "there"
    niche = lead_data.get("niche", "e-commerce")
    platform = lead_data.get("platform", "Shopify")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "Scaling Meta & Google Ads ROAS")
    has_meta = lead_data.get("has_meta_pixel", False)
    has_tiktok = lead_data.get("has_tiktok_pixel", False)
    has_ga4 = lead_data.get("has_ga4", False)
    has_google_ads = lead_data.get("has_google_ads", False)
    est_rev = lead_data.get("est_monthly_revenue", "$10k-$50k")

    prompt = f"""
You are an elite direct-response e-commerce growth strategist and copywriter writing outreach pitches for Talha Yousaf.
Talha Yousaf is a seasoned Shopify Specialist and Google & Meta Ads media buyer with verified achievements:
- Scaled Shopify brands (including Sameday Trainers UK and fashion/footwear lines) past £696,000+ in gross revenue.
- Core Flagship Offer: **Scaling Shopify stores from ~$10k/month to $30k/month within 45 days (0.5x–2x ROAS increase Guaranteed) through Google Shopping & Search Ads capture**.
- Achieved store conversion rates of up to 4.89% through CRO and fixed critical tracking leaks (Meta CAPI, Google Ads AW- tags, GA4 attribution).

Lead Store Details:
- Store Name: {store_name}
- Domain: {domain}
- Founder/Contact: {founder_name}
- Niche/Category: {niche}
- Platform: {platform}
- Target Market: {country}
- Estimated Revenue: {est_rev}
- Google Ads Active: {"Yes" if has_google_ads else "NO (Missing - Prime candidate for $10k->$30k scale via Google Shopping!)"}
- Meta Pixel Active: {"Yes" if has_meta else "NO (Missing - Losing retargeting revenue)"}
- GA4 Tracking: {"Yes" if has_ga4 else "NO (Attribution gap)"}
- Primary Opportunity Hook: {opportunity}

Output a single JSON object with two main keys:
1. "variants": Array of 5 email objects (id: 1-5, angle, subject, body).
   - Variant 1 (FLAGSHIP): "Google Ads Scaling Guarantee ($10k->$30k/mo in 45 Days)"
     * Focus on capturing high-intent Google Search/Shopping buyers vs burning money on cold ads, with 0.5-2x ROAS guarantee in 45 days.
   - Variant 2: "£696k Case Study & Social Proof Hook"
     * Focus on how Talha scaled a {niche} store past £696k revenue with structured creative testing.
   - Variant 3: "Missing Tracking & Retargeting Leak Hook"
     * Focus on {opportunity} and stopping revenue leaks.
   - Variant 4: "4.89% Conversion Rate (CRO) Quick-Win"
     * Focus on mobile checkout speed and boosting store conversion rate.
   - Variant 5: "Executive Paid Traffic Teardown"
     * Peer-to-peer executive offer for {founder_name}.

2. "multi_channel": Object containing:
   - "linkedin": {{"connection_note": "Under 280 chars tailored connection request", "inmail": "Follow up message"}}
   - "instagram": {{"dm_script": "Casual, 3-sentence hook mentioning {store_name}'s {niche} collection and the 45-day Google Ads scale guarantee"}}
   - "reddit": {{"dm_pitch": "Helpful, community-friendly DM addressing scaling pain points and sharing the 3-step Google Ads roadmap"}}
   - "loom_script": {{"video_outline": "Step-by-step 30-second Loom script outline breaking down competitors capturing their Google search keywords"}}

Tone: Authentic, peer-to-peer, executive, direct, no buzzwords. Short 1-2 sentence paragraphs.
Signature:
Best regards,
Talha Yousaf
Digital Marketer & Shopify Growth Specialist

Return ONLY valid JSON.
"""

    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.75,
                    response_mime_type="application/json"
                )
            )
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text.strip())
            if isinstance(data, dict) and "variants" in data:
                return data.get("variants", []), data.get("multi_channel", {})
            elif isinstance(data, list):
                return data, get_fallback_multi_channel(lead_data)
                
        except Exception as e:
            print(f"Gemini API generation note (using guaranteed fallback suite): {e}")

    # Fallback suite
    return get_fallback_pitches(lead_data), get_fallback_multi_channel(lead_data)

def get_fallback_pitches(lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    store_name = lead_data.get("store_name", "your brand")
    founder_name = lead_data.get("founder_name") or "there"
    niche = lead_data.get("niche", "e-commerce")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "Scaling Meta & Google Ads ROAS")
    
    return [
        {
            "id": 1,
            "angle": "Google Ads Scale Guarantee ($10k to $30k/mo in 45 Days)",
            "subject": f"scaling {store_name} from $10k to $30k/mo in 45 days (Google Ads)?",
            "body": f"Hi {founder_name},\n\nI came across {store_name} while researching high-potential {niche} brands in {country}—really impressed with your product lineup.\n\nI noticed you’re currently relying heavily on cold social traffic and missing high-intent Google Search & Shopping capture for key {niche} buyer queries.\n\nWe specialize in scaling established Shopify stores doing ~$10k/month to $30k/month within 45 days by capturing ready-to-buy search traffic through Google Shopping & PMax—with a guaranteed 0.5x to 2x ROAS increase.\n\nIf we don't hit the target ROAS within 45 days, we work completely free.\n\nWould you be open to a quick 2-minute video breakdown of how your top 3 competitors in {niche} are capturing your search sales?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Shopify Growth Specialist"
        },
        {
            "id": 2,
            "angle": "E-Commerce Growth Case Study (£696k Gross Revenue)",
            "subject": f"idea for {store_name}'s ad performance",
            "body": f"Hi {founder_name},\n\nI’ve been following {store_name}'s growth in the {niche} space in {country}.\n\nRecently, we helped an independent brand in your space scale past £696,000 in gross revenue by restructuring their Google Shopping feeds and testing high-intent ad hooks.\n\nLooking at {store_name}, I spotted 2 immediate creative angles and catalog ad structures that could help drive lower customer acquisition costs without increasing your current ad spend.\n\nWould you be open to checking out a quick 3-point growth breakdown tailored specifically for {store_name}?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 3,
            "angle": "Ad Tracking & Revenue Leak Optimization",
            "subject": f"growth opportunity for {store_name}",
            "body": f"Hi {founder_name},\n\nI was checking out {store_name}'s {niche} collection and noticed an immediate opportunity in your ad tracking infrastructure ({opportunity}).\n\nWhen we resolved this for another Shopify brand in your space, their retargeting ROAS jumped within 3 weeks because Google and Meta were finally able to attribute checkout signals and optimize for high-value repeat buyers.\n\nWould it make sense to share a brief breakdown of how we fixed this with your growth team?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 4,
            "angle": "4.89% Conversion Rate (CRO) Quick-Win",
            "subject": f"2 quick CRO tweaks for {store_name}",
            "body": f"Hi {founder_name},\n\nI was reviewing your mobile product pages for {store_name}.\n\nBy optimizing sticky Add-to-Cart layouts and streamlining checkout friction on Shopify, we've helped stores in your space push store conversion rates up to 4.89%.\n\nI put together a quick 2-point checklist specifically for {store_name}. Would you like me to send it over?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Conversion Specialist"
        },
        {
            "id": 5,
            "angle": "Executive Growth Strategy & Performance Scaling",
            "subject": f"scaling {store_name} in {country}",
            "body": f"Hi {founder_name},\n\nI'm reaching out because I specialize in helping ambitious {niche} brands scale their monthly recurring revenue profitably through Google Ads and conversion optimization.\n\nWe guarantee taking established Shopify brands from $10k/mo to $30k/mo in 45 days with a 0.5x–2x ROAS lift.\n\nWould you be open to exploring 2 quick ideas on how {store_name} can capture search buyers at a lower acquisition cost this quarter?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        }
    ]

def get_fallback_multi_channel(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    store_name = lead_data.get("store_name", "your store")
    founder_name = lead_data.get("founder_name") or "there"
    niche = lead_data.get("niche", "e-commerce")
    country = lead_data.get("country", "UK")

    return {
        "email": {
            "subject": f"scaling {store_name} from $10k to $30k/mo in 45 days (Google Ads)?",
            "body": f"Hi {founder_name},\n\nCame across {store_name} while researching top {niche} brands in {country}—loved your collection.\n\nWe specialize in scaling Shopify brands from ~$10k/month to $30k/month within 45 days through high-intent Google Shopping & Search Ads (guaranteed 0.5x–2x ROAS increase, or we work free).\n\nMind if I send over a quick 2-minute video breakdown of how your top competitors are capturing your search sales?"
        },
        "linkedin": {
            "connection_note": f"Hey {founder_name}, loved {store_name}'s {niche} collection! We help Shopify brands at ~$10k/mo scale to $30k/mo in 45 days via Google Shopping (0.5-2x ROAS boost guaranteed). Would love to connect and share a 2-min breakdown!",
            "inmail": f"Hey {founder_name}, thanks for connecting! Put together a 2-min breakdown showing how {store_name} can capture high-intent Google Shopping traffic in {country} with a guaranteed ROAS lift. Would it be okay to drop the link here?"
        },
        "instagram": {
            "dm_script": f"Hey team! Loved your {niche} collection 🙌 Quick question: are you guys currently capturing high-intent search buyers on Google Shopping? We guarantee scaling Shopify stores from $10k to $30k/mo within 45 days (0.5x-2x ROAS boost). Would you be open to a 2-min breakdown showing how?"
        },
        "reddit": {
            "dm_pitch": f"Hey! Saw your post regarding scaling your Shopify store and managing ad performance. One thing that consistently helps our e-com clients scale from $10k/mo to $30k/mo in 45 days is capturing search intent via Google Shopping/PMax with a 0.5-2x ROAS boost. Happy to share our 3-step roadmap if helpful—no pitch, just actionable steps."
        },
        "loom_script": {
            "video_outline": f"1. (0-5s) Showcase {store_name}'s top product & compliment aesthetic.\n2. (5-15s) Show Google Search results where competitors in {niche} are bidding on their keywords.\n3. (15-25s) Present the 45-day roadmap: Google Shopping feed optimization + PMax scale to go from $10k to $30k/mo with 0.5-2x ROAS guarantee.\n4. (25-30s) Call to action: 'Let me know if you'd like me to send the full keyword map.'"
        }
    }

