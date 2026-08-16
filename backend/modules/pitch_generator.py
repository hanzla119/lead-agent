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
You are an elite, world-class direct-response e-commerce copywriter writing cold outreach emails for Talha Yousaf.
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

Variant 1: "The Technical & Pixel Leak Hook"
- Subject line: Curiosity-driven, under 45 chars (e.g., "quick question about {store_name}'s pixel", "noticed a tracking gap on {store_name}")
- Body: Pattern interrupt, mentions {store_name}, points out the missing pixel or tracking leak without being rude, explains how resolving it recaptures lost cart abandoners, soft CTA.

Variant 2: "The £696k Case Study & Social Proof Hook"
- Subject line: Intriguing, under 45 chars (e.g., "scaling {store_name} in {country}", "how we scaled a {niche} brand to £696k")
- Body: Shares how Talha scaled a {niche} brand to £696,000+ gross sales using structured creative testing and Performance Max, offers to share 2 specific ad angles for {store_name}.

Variant 3: "High-Converting TikTok & Reels Creative Hook"
- Subject line: Punchy, under 45 chars (e.g., "3 TikTok ad concepts for {store_name}", "creative idea for {store_name}")
- Body: Focuses on viral, high-ROAS TikTok & Meta video concepts tailored to {niche} buyers, offers to send over 3 customized storyboards/hooks for free.

Variant 4: "The 4.89% Conversion Rate (CRO) Quick-Win"
- Subject line: Specific & value-led, under 45 chars (e.g., "2 CRO tweaks for {store_name}", "{store_name} - mobile checkout note")
- Body: Focuses on Shopify store speed, sticky add-to-cart, and checkout friction (referencing optimizing stores up to 4.89% conversion rate), offers a 2-point checklist.

Variant 5: "The Free 2-Minute Video Breakdown Hook"
- Subject line: Ultra-personal, under 45 chars (e.g., "recorded a 2-min video for {store_name}", "quick video for the {store_name} team")
- Body: Ultra low-pressure, offers a recorded 2-minute video breakdown showing the biggest growth opportunity on their store, zero sales pitch upfront.

Guidelines for all variants:
- Casual, authentic, executive tone (no cringe buzzwords like "synergy", "game-changer", "skyrocket").
- Short paragraphs (1-2 sentences per paragraph for effortless mobile reading).
- Soft, frictionless call to action (e.g., "Open to checking out the concepts?", "Mind if I send over the 2-minute video?").
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

    # 5 Master-class fallback templates if API key is not configured or rate limited
    return get_fallback_pitches(lead_data)

def get_fallback_pitches(lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    store_name = lead_data.get("store_name", "your brand")
    niche = lead_data.get("niche", "e-commerce")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "Missing Meta Pixel tracking")
    
    return [
        {
            "id": 1,
            "angle": "Tracking & Revenue Leak Audit",
            "subject": f"quick question about {store_name}'s pixel",
            "body": f"Hi {store_name} Team,\n\nI was checking out your {niche} collection and really liked the product line.\n\nWhile browsing your storefront, I noticed a quick technical gap: {opportunity}.\n\nWhen we resolved this for another {niche} brand in the {country}, their retargeting ROAS jumped within 3 weeks because Meta & Google were finally attributing checkout signals accurately.\n\nWould you be open to a quick 2-minute video showing where this leak is happening and how to fix it?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 2,
            "angle": "£696k Scale & Case Study Proof",
            "subject": f"how we scaled a {niche} store past £696k",
            "body": f"Hi team at {store_name},\n\nI recently helped scale an e-commerce brand in the {niche} space past £696,000 in gross revenue by restructuring their Meta and Google Performance Max ad campaigns.\n\nLooking at {store_name}, I spotted 2 immediate creative angles and catalog ad structures that could drive lower customer acquisition costs without bloating your ad spend.\n\nMind if I send over a quick 3-point breakdown tailored to {store_name}?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Shopify Specialist"
        },
        {
            "id": 3,
            "angle": "Viral TikTok & Reels Ad Concepts",
            "subject": f"3 TikTok ad concepts for {store_name}",
            "body": f"Hi {store_name} Team,\n\nI love what you're doing with your {niche} catalog.\n\nWe specialize in high-converting TikTok & Meta short-form creatives that turn casual scrollers into repeat buyers.\n\nI mapped out 3 specific ad hooks designed for {store_name}'s audience that test great for impulse purchases. Would it be alright if I emailed them over for you to review?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 4,
            "angle": "4.89% Conversion Rate (CRO) Quick-Win",
            "subject": f"2 quick CRO tweaks for {store_name}",
            "body": f"Hi {store_name} Team,\n\nI was looking at your mobile product pages for {store_name}.\n\nBy optimizing sticky Add-to-Cart layouts and streamlining checkout friction on Shopify, we've helped stores in your space push store conversion rates up to 4.89%.\n\nI put together a quick 2-point checklist specifically for {store_name}. Would you like me to send it over?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Conversion Specialist"
        },
        {
            "id": 5,
            "angle": "Free 2-Minute Video Breakdown",
            "subject": f"recorded a 2-min video for {store_name}",
            "body": f"Hi there,\n\nI put together a short 2-minute video sharing 3 growth opportunities I spotted on {store_name} regarding paid ads and conversion rates.\n\nNo sales pitch or expectation at all—just some actionable insights that helped similar {niche} brands scale in the {country}.\n\nWould you mind if I sent the video link over for you to review?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        }
    ]
