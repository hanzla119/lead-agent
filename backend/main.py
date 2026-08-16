import os
import csv
import io
import json
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from backend.config import SENDER_EMAIL, SENDER_NAME, GEMINI_MODEL
from backend.models import (
    CampaignRequest,
    CampaignStatus,
    EmailSendRequest,
    BatchSendRequest,
    TestEmailRequest,
    Lead
)
from backend.database import (
    init_db,
    save_lead,
    get_all_leads,
    get_lead_by_id,
    update_lead_status,
    log_email_send,
    get_stats
)
from backend.modules.discovery import discover_leads
from backend.modules.auditor import audit_website
from backend.modules.enricher import enrich_store_contacts
from backend.modules.pitch_generator import generate_pitches_with_gemini
from backend.modules.mailer import send_single_email_async, send_test_email_sync, wait_rate_limit_delay

# Initialize Database
init_db()

app = FastAPI(title="Lead Generation & Outreach Agent", version="1.0.0")

# Enable CORS for cross-origin or local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket Connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# Global State for active background tasks
ACTIVE_CAMPAIGN: Optional[Dict[str, Any]] = None
ACTIVE_SENDING_QUEUE: bool = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background Pipeline Execution
async def run_lead_generation_pipeline(campaign_id: str, req: CampaignRequest):
    global ACTIVE_CAMPAIGN
    
    ACTIVE_CAMPAIGN = {
        "id": campaign_id,
        "niche": req.niche,
        "platform": req.platform,
        "country": req.country,
        "target_count": req.target_count,
        "status": "running",
        "leads_found": 0,
        "leads_contactable": 0,
        "emails_sent": 0,
        "current_step": "Starting discovery engine...",
        "progress_percentage": 5,
        "logs": [f"🚀 Initiated campaign for niche '{req.niche}' on platform '{req.platform}' ({req.country}) with target {req.target_count} leads."],
        "created_at": datetime.utcnow().isoformat()
    }
    await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})

    try:
        # 1. DISCOVERY
        ACTIVE_CAMPAIGN["current_step"] = f"Searching web for '{req.niche}' {req.platform} stores..."
        ACTIVE_CAMPAIGN["progress_percentage"] = 15
        await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})

        candidates = discover_leads(
            niche=req.niche,
            platform=req.platform,
            country=req.country,
            limit=req.target_count
        )
        
        ACTIVE_CAMPAIGN["logs"].append(f"🔍 Discovered {len(candidates)} potential store candidates.")
        ACTIVE_CAMPAIGN["leads_found"] = len(candidates)
        ACTIVE_CAMPAIGN["progress_percentage"] = 30
        await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})

        # 2. AUDIT, ENRICH & PITCH GENERATION
        total_candidates = len(candidates)
        if total_candidates == 0:
            ACTIVE_CAMPAIGN["status"] = "completed"
            ACTIVE_CAMPAIGN["current_step"] = "No additional stores found for this exact query."
            ACTIVE_CAMPAIGN["progress_percentage"] = 100
            await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})
            return

        for idx, cand in enumerate(candidates):
            domain = cand["domain"]
            store_name = cand["store_name"]
            url = cand["url"]

            ACTIVE_CAMPAIGN["current_step"] = f"[{idx+1}/{total_candidates}] Auditing & Enriching {domain}..."
            ACTIVE_CAMPAIGN["progress_percentage"] = int(30 + ((idx + 1) / total_candidates) * 65)
            await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})

            # Audit Website
            audit_res, html_content = audit_website(url)
            
            # Enrich Contacts
            enrich_res = enrich_store_contacts(url, initial_html=html_content)

            # Combine lead data
            lead_dict = {
                "domain": domain,
                "store_name": store_name,
                "url": url,
                "niche": req.niche,
                "platform": audit_res.get("platform") or req.platform,
                "country": req.country,
                "email": enrich_res.get("email"),
                "email_status": enrich_res.get("email_status", "not_found"),
                "phone": enrich_res.get("phone"),
                "instagram": enrich_res.get("instagram"),
                "linkedin": enrich_res.get("linkedin"),
                "facebook": enrich_res.get("facebook"),
                "tiktok": enrich_res.get("tiktok"),
                "founder_name": enrich_res.get("founder_name"),
                "has_meta_pixel": audit_res.get("has_meta_pixel", False),
                "has_ga4": audit_res.get("has_ga4", False),
                "has_tiktok_pixel": audit_res.get("has_tiktok_pixel", False),
                "audit_notes": audit_res.get("audit_notes", ""),
                "primary_opportunity": audit_res.get("primary_opportunity", ""),
                "pitch_variants": [],
                "selected_pitch_index": 0,
                "review_status": "pending"
            }

            if enrich_res.get("email"):
                ACTIVE_CAMPAIGN["leads_contactable"] += 1
                ACTIVE_CAMPAIGN["logs"].append(f"📧 Found verified email for {store_name} ({enrich_res['email']}). Generating Gemini AI pitches...")
                await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})
                
                # Generate AI Pitches
                pitches = generate_pitches_with_gemini(lead_dict)
                lead_dict["pitch_variants"] = pitches
            else:
                ACTIVE_CAMPAIGN["logs"].append(f"ℹ️ {store_name}: Scraped technical audit ({lead_dict['primary_opportunity']}), no public email found.")

            # Save to Database
            save_lead(lead_dict)
            await manager.broadcast({"type": "lead_discovered", "data": lead_dict})
            await asyncio.sleep(0.3)

        ACTIVE_CAMPAIGN["status"] = "completed"
        ACTIVE_CAMPAIGN["current_step"] = "Lead generation pipeline completed!"
        ACTIVE_CAMPAIGN["progress_percentage"] = 100
        ACTIVE_CAMPAIGN["logs"].append(f"✅ Finished! Found {ACTIVE_CAMPAIGN['leads_found']} stores, {ACTIVE_CAMPAIGN['leads_contactable']} ready for review.")
        await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})

    except Exception as e:
        if ACTIVE_CAMPAIGN:
            ACTIVE_CAMPAIGN["status"] = "error"
            ACTIVE_CAMPAIGN["current_step"] = f"Error: {str(e)}"
            ACTIVE_CAMPAIGN["logs"].append(f"❌ Pipeline error: {str(e)}")
            await manager.broadcast({"type": "campaign_update", "data": ACTIVE_CAMPAIGN})

# API Routes
@app.post("/api/campaign/start")
async def start_campaign(req: CampaignRequest, background_tasks: BackgroundTasks):
    campaign_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_lead_generation_pipeline, campaign_id, req)
    return {"message": "Campaign started", "campaign_id": campaign_id}

@app.get("/api/campaign/status")
async def get_campaign_status():
    global ACTIVE_CAMPAIGN
    return ACTIVE_CAMPAIGN or {"status": "idle"}

@app.get("/api/leads")
async def fetch_leads(
    privacy_mode: bool = Query(False),
    filter_status: Optional[str] = Query("all")
):
    leads = get_all_leads(privacy_mode=privacy_mode, filter_status=filter_status)
    return leads

@app.get("/api/leads/{lead_id}")
async def fetch_lead_detail(lead_id: int):
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.post("/api/leads/{lead_id}/review")
async def review_lead(
    lead_id: int,
    payload: Dict[str, Any]
):
    status = payload.get("status", "approved")
    selected_pitch = payload.get("selected_pitch_index", 0)
    custom_variants = payload.get("pitch_variants", None)
    
    update_lead_status(lead_id, status, selected_pitch=selected_pitch, custom_variants=custom_variants)
    return {"message": f"Lead {lead_id} updated to {status}"}

@app.post("/api/leads/batch-review")
async def batch_review_leads(payload: Dict[str, Any]):
    lead_ids = payload.get("lead_ids", [])
    status = payload.get("status", "approved")
    for lid in lead_ids:
        update_lead_status(lid, status)
    return {"message": f"Updated {len(lead_ids)} leads to {status}"}

@app.post("/api/outreach/send-single")
async def send_single_lead_email(req: EmailSendRequest):
    lead = get_lead_by_id(req.lead_id)
    if not lead or not lead.get("email"):
        raise HTTPException(status_code=400, detail="Lead does not have a valid email")

    # Pick pitch
    subject = req.custom_subject
    body = req.custom_body

    if not subject or not body:
        variants = lead.get("pitch_variants", [])
        if variants and 0 <= req.variant_id < len(variants):
            chosen = variants[req.variant_id]
            subject = chosen.get("subject", "E-commerce Growth Opportunity")
            body = chosen.get("body", "")
        else:
            subject = f"Growth opportunity for {lead['store_name']}"
            body = f"Hi {lead['store_name']},\n\nWould you be open to discussing scaling your online sales?\n\nBest regards,\nTalha Yousaf"

    res = await send_single_email_async(lead["email"], subject, body)
    if res["success"]:
        update_lead_status(req.lead_id, "sent")
        log_email_send(req.lead_id, lead["email"], subject, body, "sent")
        return {"success": True, "message": f"Email successfully sent to {lead['email']}"}
    else:
        update_lead_status(req.lead_id, "failed")
        log_email_send(req.lead_id, lead["email"], subject, body, "failed", res["error"])
        return {"success": False, "error": res["error"]}

async def run_batch_sending(lead_ids: List[int], delay_sec: int):
    global ACTIVE_SENDING_QUEUE
    ACTIVE_SENDING_QUEUE = True
    
    total = len(lead_ids)
    for idx, lid in enumerate(lead_ids):
        lead = get_lead_by_id(lid)
        if not lead or not lead.get("email"):
            continue
            
        var_idx = lead.get("selected_pitch_index", 0)
        variants = lead.get("pitch_variants", [])
        if variants and 0 <= var_idx < len(variants):
            chosen = variants[var_idx]
            subject = chosen.get("subject", "E-commerce Growth Strategy")
            body = chosen.get("body", "")
        else:
            subject = f"Marketing idea for {lead['store_name']}"
            body = f"Hi,\n\nI wanted to share a quick idea for {lead['store_name']}.\n\nBest,\nTalha Yousaf"

        await manager.broadcast({
            "type": "sending_progress",
            "message": f"[{idx+1}/{total}] Sending email to {lead['store_name']} ({lead['email']})...",
            "current": idx + 1,
            "total": total
        })

        res = await send_single_email_async(lead["email"], subject, body)
        if res["success"]:
            update_lead_status(lid, "sent")
            log_email_send(lid, lead["email"], subject, body, "sent")
        else:
            update_lead_status(lid, "failed")
            log_email_send(lid, lead["email"], subject, body, "failed", res["error"])

        if idx < total - 1:
            await wait_rate_limit_delay(delay_sec, delay_sec + 10)

    ACTIVE_SENDING_QUEUE = False
    await manager.broadcast({
        "type": "sending_complete",
        "message": f"✅ Batch outreach complete for {total} leads."
    })

@app.post("/api/outreach/send-batch")
async def send_batch_emails(req: BatchSendRequest, background_tasks: BackgroundTasks):
    global ACTIVE_SENDING_QUEUE
    if ACTIVE_SENDING_QUEUE:
        raise HTTPException(status_code=400, detail="Another batch send is currently running.")
    background_tasks.add_task(run_batch_sending, req.lead_ids, req.delay_seconds)
    return {"message": f"Queued {len(req.lead_ids)} emails for sequential rate-limited sending."}

@app.post("/api/outreach/test-email")
async def test_email_endpoint(req: TestEmailRequest):
    res = send_test_email_sync(req.target_email, req.subject, req.message)
    return res

@app.get("/api/stats")
async def fetch_stats():
    return get_stats()

@app.get("/api/export/csv")
async def export_csv(privacy_mode: bool = Query(False)):
    leads = get_all_leads(privacy_mode=privacy_mode)
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "ID", "Store Name", "Domain", "URL", "Niche", "Platform", "Country",
        "Email", "Email Status", "Phone", "Instagram", "LinkedIn", "TikTok",
        "Meta Pixel", "GA4", "TikTok Pixel", "Primary Opportunity", "Review Status", "Sent Date"
    ]
    writer.writerow(headers)
    
    for l in leads:
        writer.writerow([
            l.get("id"),
            l.get("store_name"),
            l.get("domain"),
            l.get("url"),
            l.get("niche"),
            l.get("platform"),
            l.get("country"),
            l.get("email"),
            l.get("email_status"),
            l.get("phone"),
            l.get("instagram"),
            l.get("linkedin"),
            l.get("tiktok"),
            "Yes" if l.get("has_meta_pixel") else "No",
            "Yes" if l.get("has_ga4") else "No",
            "Yes" if l.get("has_tiktok_pixel") else "No",
            l.get("primary_opportunity"),
            l.get("review_status"),
            l.get("send_timestamp") or ""
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
    )

# Static files for frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Lead Agent API Running. Frontend directory initializing."}
