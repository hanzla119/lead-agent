import json
from typing import List, Dict, Any
from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

def generate_pitches_with_gemini(lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calls Google Gemini AI to craft 3 unique, high-converting pitch variants
    tailored to the store's audit findings and Talha Yousaf's proven e-commerce achievements.
    """
    store_name = lead_data.get("store_name", "your store")
    niche = lead_data.get("niche", "e-commerce")
    platform = lead_data.get("platform", "Shopify")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "Scaling Meta & Google Ads ROAS")
    has_meta = lead_data.get("has_meta_pixel", False)
    has_tiktok = lead_data.get("has_tiktok_pixel", False)

    prompt = f"""
You are an expert e-commerce copywriter writing cold outreach emails for Talha Yousaf, an elite digital marketer and Shopify specialist who has scaled e-commerce brands (including footwear & fashion brands like Sameday Trainers UK and others) to over £696,000+ in revenue across Meta, Google, and TikTok ads.

Lead Details:
- Store Name: {store_name}
- Niche/Category: {niche}
- Platform: {platform}
- Target Market/Country: {country}
- Meta Pixel Present: {"Yes" if has_meta else "NO (Missing - critical retargeting leak!)"}
- TikTok Pixel Present: {"Yes" if has_tiktok else "NO (Untapped Gen-Z audience)"}
- Identified Opportunity / Hook: {opportunity}

Generate exactly 3 distinct, highly personalized cold outreach pitch variants in JSON format.
Each variant must have:
1. "id": number (1, 2, 3)
2. "angle": A short label (e.g., "Meta Pixel / CRO Leak", "£696k Scale Case Study", "Quick-Win Ad Creative Strategy")
3. "subject": An irresistible, curiosity-driven subject line UNDER 50 characters (e.g., "Quick question about {store_name}'s pixel", "Idea for {store_name}'s ads in {country}", "Noticed a quick fix for {store_name}")
4. "body": An engaging, professional, non-spammy email body (3-4 concise paragraphs) that:
   - Mentions {store_name} specifically.
   - Mentions the relevant audit hook or relevant case study (e.g., scaling UK footwear/apparel brands to £696k+ gross sales with high ROAS).
   - Ends with a low-friction, casual call to action (e.g., "Would you be open to a 2-minute video breakdown?" or "Mind if I share 2 ad angles that worked for similar stores?").
   - Signature: "Best regards,\\nTalha Yousaf\\nDigital Marketer & E-Commerce Specialist"

Return ONLY a valid JSON array of 3 objects with keys: id, angle, subject, body. Do not include markdown code block formatting if possible, just raw JSON or json markdown block.
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )
        
        text = response.text.strip()
        # Clean any accidental markdown backticks
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        variants = json.loads(text.strip())
        if isinstance(variants, list) and len(variants) > 0:
            return variants
            
    except Exception as e:
        print(f"Gemini API generation error (using fallback): {e}")

    # Fallback high-converting templates if API fails or rate-limited
    return get_fallback_pitches(lead_data)

def get_fallback_pitches(lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    store_name = lead_data.get("store_name", "your brand")
    niche = lead_data.get("niche", "e-commerce")
    country = lead_data.get("country", "UK")
    opportunity = lead_data.get("primary_opportunity", "scaling ads")
    
    return [
        {
            "id": 1,
            "angle": "Tracking & Revenue Leak Audit",
            "subject": f"Quick question about {store_name}'s pixel setup",
            "body": f"Hi team at {store_name},\n\nI was browsing your {niche} collection and loved the product curation. While looking at the site, I noticed a quick technical gap: {opportunity}.\n\nWhen we resolved this for another {niche} brand in the {country}, their retargeting ROAS jumped within 3 weeks because Meta & Google were finally attributing checkout signals accurately.\n\nWould you be open to a quick 2-minute video showing where this leak is happening and how to fix it?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        },
        {
            "id": 2,
            "angle": "£696k Scale & Case Study Proof",
            "subject": f"Idea for scaling {store_name} in {country}",
            "body": f"Hi {store_name} Team,\n\nI recently helped scale an e-commerce brand in the {niche} space past £696,000 in gross revenue by restructuring their Meta and Google Performance Max ad campaigns.\n\nLooking at {store_name}, I spotted 2 immediate creative angles and catalog ad structures that could drive lower customer acquisition costs without bloating your ad spend.\n\nMind if I send over a quick 3-point breakdown tailored to {store_name}?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Shopify Specialist"
        },
        {
            "id": 3,
            "angle": "Quick-Win ROAS & Ad Creative Angle",
            "subject": f"2 ad concepts for {store_name}",
            "body": f"Hi there,\n\nI came across {store_name} while researching leading {niche} stores and was really impressed by your catalog.\n\nWe specialize in high-converting TikTok & Meta creatives combined with conversion rate optimization (CRO) on Shopify.\n\nI put together 2 specific ad hooks designed for {store_name}'s audience. Would it be alright if I emailed them over for you to review?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist"
        }
    ]
