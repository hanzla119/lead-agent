from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PitchVariant(BaseModel):
    id: int = 1
    angle: str  # e.g., "Google Ads Scale Guarantee ($10k->$30k/mo)", "Missing Meta Pixel Leak", "£696k Scale Case Study"
    subject: str
    body: str

class MultiChannelPitches(BaseModel):
    email: Optional[Dict[str, str]] = None          # {"subject": "...", "body": "..."}
    linkedin: Optional[Dict[str, str]] = None       # {"connection_note": "...", "inmail": "..."}
    instagram: Optional[Dict[str, str]] = None      # {"dm_script": "..."}
    reddit: Optional[Dict[str, str]] = None         # {"dm_pitch": "..."}
    loom_script: Optional[Dict[str, str]] = None    # {"video_outline": "...", "hook": "..."}

class LeadCreate(BaseModel):
    domain: str
    store_name: str
    url: str
    niche: str
    platform: str = "Shopify"
    country: str = "UK"
    
    # Value & Opportunity Scoring
    est_monthly_revenue: str = "$10k-$50k"  # '<$10k', '$10k-$50k', '$50k-$250k', '$250k+'
    lead_score: int = 50                    # 0 to 100
    lead_tier: str = "Silver"               # Bronze, Silver, Gold, Platinum
    
    # Contact & Founder
    founder_name: Optional[str] = None
    founder_title: Optional[str] = "Founder & Owner"
    email: Optional[str] = None
    email_status: str = "not_found"
    phone: Optional[str] = None
    
    # Social & Ads
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    reddit_username: Optional[str] = None
    has_google_ads: bool = False
    has_meta_pixel: bool = False
    has_ga4: bool = False
    has_tiktok_pixel: bool = False
    has_active_meta_ads: bool = False
    active_ad_count: int = 0
    
    # Audit & Pitch
    audit_notes: str = ""
    primary_opportunity: str = ""
    pitch_variants: List[PitchVariant] = []
    multi_channel_pitches: Optional[Dict[str, Any]] = None
    selected_pitch_index: int = 0
    review_status: str = "pending"  # pending, approved, rejected, sent, failed
    tags: List[str] = []

class Lead(LeadCreate):
    id: int
    created_at: str
    send_timestamp: Optional[str] = None

class CampaignRequest(BaseModel):
    niche: str = Field(..., description="E.g., shoes, fashion, fitness, supplements, jewelry")
    platform: str = Field("Shopify", description="Shopify, WooCommerce, Instagram, LinkedIn, Facebook")
    country: str = Field("UK", description="UK, US, EU, AU, CA, PK")
    target_count: int = Field(10, description="10, 50, 100, 200")
    auto_approve: bool = Field(False, description="Automatically approve verified email leads into the outreach queue")
    custom_keywords: Optional[str] = None


class CampaignStatus(BaseModel):
    id: str
    niche: str
    platform: str
    country: str
    target_count: int
    status: str  # idle, running, completed, error
    leads_found: int = 0
    leads_contactable: int = 0
    emails_sent: int = 0
    current_step: str = ""
    progress_percentage: int = 0
    logs: List[str] = []
    created_at: str

class EmailSendRequest(BaseModel):
    lead_id: int
    variant_id: int
    custom_subject: Optional[str] = None
    custom_body: Optional[str] = None

class BatchSendRequest(BaseModel):
    lead_ids: List[int]
    delay_seconds: int = 30

class TestEmailRequest(BaseModel):
    target_email: str
    subject: str = "Test Outreach Connection - Marketing by Talha"
    message: str = "This is a live test from your Autonomous Lead Agent platform."

class LeadSearchRequest(BaseModel):
    query: Optional[str] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    value_tier: Optional[str] = None
    has_google_ads: Optional[bool] = None
    has_meta_pixel: Optional[bool] = None
    channel: Optional[str] = None  # email, linkedin, instagram, reddit
    niche: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    sort_by: str = "id"  # id, lead_score, store_name, est_monthly_revenue
    sort_order: str = "DESC"

class TagUpdateRequest(BaseModel):
    tags: List[str]

class BulkActionRequest(BaseModel):
    lead_ids: List[int]
    action: str  # 'approve', 'reject', 'delete', 'tag'
    tag_name: Optional[str] = None

class LeadUpdateRequest(BaseModel):
    store_name: Optional[str] = None
    founder_name: Optional[str] = None
    founder_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    est_monthly_revenue: Optional[str] = None
    deal_value: Optional[str] = None
    lead_score: Optional[int] = None
    lead_tier: Optional[str] = None
    review_status: Optional[str] = None  # pending, approved, sent, replied, interested, booked, won, rejected
    notes: Optional[str] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    reddit_username: Optional[str] = None
    primary_opportunity: Optional[str] = None
    tags: Optional[List[str]] = None


