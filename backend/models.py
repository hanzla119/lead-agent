from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PitchVariant(BaseModel):
    id: int = 1
    angle: str  # e.g., "Missing Meta Pixel Leak", "£696k Scale Case Study", "Quick-Win ROAS Fix"
    subject: str
    body: str

class LeadCreate(BaseModel):
    domain: str
    store_name: str
    url: str
    niche: str
    platform: str = "Shopify"
    country: str = "UK"
    email: Optional[str] = None
    email_status: str = "not_found"
    phone: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    founder_name: Optional[str] = None
    has_meta_pixel: bool = False
    has_ga4: bool = False
    has_tiktok_pixel: bool = False
    audit_notes: str = ""
    primary_opportunity: str = ""
    pitch_variants: List[PitchVariant] = []
    selected_pitch_index: int = 0
    review_status: str = "pending"  # pending, approved, rejected, sent, failed

class Lead(LeadCreate):
    id: int
    created_at: str
    send_timestamp: Optional[str] = None

class CampaignRequest(BaseModel):
    niche: str = Field(..., description="E.g., shoes, fashion, fitness, supplements")
    platform: str = Field("Shopify", description="Shopify, WooCommerce, Instagram, LinkedIn, Facebook")
    country: str = Field("UK", description="UK, US, EU, AU, CA, PK")
    target_count: int = Field(10, description="10, 50, 100, 200")
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
