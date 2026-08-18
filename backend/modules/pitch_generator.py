import json
from typing import List, Dict, Any
from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

def generate_pitches_with_gemini(lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calls Google Gemini AI to craft 5 irresistible, hyper-personalized pitch variants
    tailored to the store's audit findings and Talha Yousaf's verified e-commerce achievements (£696k+ revenue, 4.89% CRO, Sameday Trainers UK, Shine IN).
    """
    store_name = lead_data.get("store_name", "your store")
    niche = lead_data.get("niche", "e-commerce")
    platform = lead_data.get("platform", "Shopify")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "Scaling Meta & Google Ads ROAS")
    has_meta = lead_data.get("has_meta_pixel", False)
    has_tiktok = lead_data.get("has_tiktok_pixel", False)
    has_ga4 = lead_data.get("has_ga4", False)

    prompt = f"""
You are an elite direct-response e-commerce copywriter writing cold outreach emails for Talha Yousaf.
Talha Yousaf is a seasoned Digital Marketer, Shopify Specialist, and Paid Media Strategist with verified track records:
- Scaled UK & international e-commerce stores (including footwear/apparel brands like Sameday Trainers UK and fashion lines) past £696,000+ in gross revenue.
- Achieved exceptional e-commerce conversion rates of up to 4.89% through CRO (Conversion Rate Optimization) and structured ad testing on Meta, Google Shopping/PMax, and TikTok Ads.
- Specializes in fixing tracking leaks (Meta CAPI, TikTok pixel, GA4 attribution) and creating high-converting creative ad hooks.

Lead Store Details:
- Store Name: {store_name}
- Niche/Category: {niche}
- Platform: {platform}
- Target Country: {country}
- Meta Pixel Present: {"Yes" if has_meta else "NO (Missing - Critical retargeting & iOS 14+ revenue leak!)"}
- TikTok Pixel Present: {"Yes" if has_tiktok else "NO (Missing - Untapped Gen-Z/impulse demographic!)"}
- GA4 / GTM Tracking: {"Yes" if has_ga4 else "NO (Attribution gap)"}
- Identified Audit Hook: {opportunity}

Generate exactly 5 distinct, psychological, high-converting cold email pitch variants in JSON format.

Variant 1: "The £696k Case Study & Social Proof Hook"
- Subject line: Engaging & professional, under 45 chars (e.g., "idea for {store_name}'s ad performance", "how we scaled a {niche} brand past £696k")
- Body: Shares how Talha helped scale a {niche} brand past £696,000+ in gross revenue using structured creative testing and Performance Max, offers to share a 3-point growth brief tailored for {store_name}.
- CTA: "Would you be open to seeing the 3-point growth breakdown tailored specifically for {store_name}?"

Variant 2: "The Tracking & Retargeting Revenue Optimization Hook"
- Subject line: Curiosity-driven & value-focused (e.g., "growth opportunity for {store_name}", "quick note regarding {store_name}'s checkout")
- Body: Compliments the {niche} collection, points out the tracking/attribution opportunity ({opportunity}), explains how fixing this increased ROAS within 3 weeks for a similar brand by accurately attributing high-value buyers.
- CTA: "Would it make sense to share a brief breakdown of how we fixed this with your growth team?"

Variant 3: "High-Converting Creative Hooks & Ad Angles"
- Subject line: Punchy & creative (e.g., "3 ad concepts for {store_name}", "creative idea for {store_name}")
- Body: Focuses on high-converting TikTok & Meta ad creatives/hooks designed specifically for {niche} buyers to lower customer acquisition cost (CAC).
- CTA: "Mind if I email the 3 concepts over for your team to check out?"

Variant 4: "The 4.89% Conversion Rate (CRO) Quick-Win"
- Subject line: Specific & value-led (e.g., "2 CRO tweaks for {store_name}", "{store_name} - mobile checkout note")
- Body: Focuses on Shopify mobile speed, sticky Add-to-Cart layouts, and reducing checkout drop-offs (referencing optimizing stores up to 4.89% conversion rate).
- CTA: "Would you like me to send the 2-point CRO checklist over?"

Variant 5: "Executive Growth Strategy & Ad Scaling"
- Subject line: Executive & tailored (e.g., "scaling {store_name} in {country}", "quick question for {store_name} team")
- Body: Introduces Talha's performance-driven growth framework for ambitious {niche} brands to scale monthly revenue while cutting ad spend waste.
- CTA: "Would you be open to exploring 2 quick ideas on how {store_name} can acquire customers at a lower cost this quarter?"

STRICT GUIDELINES:
- DO NOT use the phrase "Would you be open to a quick 2-minute video showing where this leak is happening and how to fix it?". Use the varied, natural, executive CTAs listed above.
- Tone: Casual, authentic, peer-to-peer executive tone (no cringe buzzwords like "synergy", "game-changer", "skyrocket").
- Short paragraphs (1-2 sentences per paragraph for effortless mobile reading).
- Signature:
  Best regards,
  Talha Yousaf
  Digital Marketer & E-Commerce Specialist

Return ONLY a valid JSON array of 5 objects with keys: "id" (1 to 5), "angle", "subject", "body".
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
                
            variants = json.loads(text.strip())
            if isinstance(variants, list) and len(variants) >= 3:
                return variants
                
        except Exception as e:
            print(f"Gemini API generation error (using enhanced 5-variant fallback): {e}")

    # 5 Master-class fallback templates
    return get_fallback_pitches(lead_data)

def get_fallback_pitches(lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    store_name = lead_data.get("store_name", "your brand")
    niche = lead_data.get("niche", "e-commerce")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "Missing Meta Pixel tracking")
    
    return [
        {
            "id": 1,
            "angle": "£696k Scale & Case Study Proof",
            "subject": f"idea for {store_name}'s ad performance",
            "body": f"Hi {store_name} Team,\n\nI recently helped scale an independent {niche} brand past £696,000 in gross revenue by restructuring their Meta and Google Performance Max campaigns around high-intent buyers.\n\nLooking at {store_name}, I spotted 2 immediate creative angles and catalog ad structures that could drive lower customer acquisition costs (CAC) without increasing your current ad spend.\n\nWould you be open to seeing the 3-point growth breakdown tailored specifically for {store_name}?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 2,
            "angle": "Tracking & Revenue Leak Audit",
            "subject": f"growth opportunity for {store_name}",
            "body": f"Hi {store_name} Team,\n\nI was checking out {store_name}'s {niche} collection and really loved your product lineup.\n\nWhile reviewing your storefront, I noticed a key opportunity around your ad tracking and attribution setup ({opportunity}).\n\nWhen we resolved this for another brand in your space, their retargeting ROAS jumped within 3 weeks because Meta and Google were finally able to attribute checkout signals and optimize for high-value repeat customers.\n\nWould it make sense to share a brief breakdown of how we fixed this with your growth team?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 3,
            "angle": "Viral TikTok & Reels Ad Concepts",
            "subject": f"3 ad concepts for {store_name}",
            "body": f"Hi team at {store_name},\n\nI’ve been following {store_name}'s growth in the {country} {niche} market and love your brand aesthetic.\n\nWe specialize in developing high-converting short-form ad creatives and UGC hooks that turn casual scrollers into profitable first-time buyers.\n\nI mapped out 3 specific ad concepts and hook angles designed specifically for {store_name}'s customer demographic. Mind if I email the 3 concepts over for your marketing team to review?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Shopify Specialist"
        },
        {
            "id": 4,
            "angle": "4.89% Conversion Rate (CRO) Quick-Win",
            "subject": f"2 quick CRO tweaks for {store_name}",
            "body": f"Hi {store_name} Team,\n\nI was reviewing your mobile product pages for {store_name}.\n\nBy optimizing sticky Add-to-Cart layouts and streamlining checkout friction on Shopify, we've helped stores in your space push store conversion rates up to 4.89%.\n\nI put together a quick 2-point checklist specifically for {store_name}. Would you like me to send it over?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Conversion Specialist"
        },
        {
            "id": 5,
            "angle": "Executive Growth Strategy & Ad Scaling",
            "subject": f"scaling {store_name} in {country}",
            "body": f"Hi {store_name} Team,\n\nI'm reaching out because I specialize in helping ambitious {niche} brands scale their monthly recurring revenue profitably through paid media and conversion optimization.\n\nWe recently helped a brand in your category scale past £696k+ in gross sales by testing dynamic creative variations and eliminating ad spend waste.\n\nWould you be open to exploring 2 quick ideas on how {store_name} can acquire customers at a lower cost this quarter?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        }
    ]
