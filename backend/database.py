import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Leads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        store_name TEXT,
        url TEXT,
        niche TEXT,
        platform TEXT,
        country TEXT,
        email TEXT,
        email_status TEXT DEFAULT 'not_found',
        phone TEXT,
        instagram TEXT,
        linkedin TEXT,
        facebook TEXT,
        tiktok TEXT,
        founder_name TEXT,
        has_meta_pixel INTEGER DEFAULT 0,
        has_ga4 INTEGER DEFAULT 0,
        has_tiktok_pixel INTEGER DEFAULT 0,
        audit_notes TEXT DEFAULT '',
        primary_opportunity TEXT DEFAULT '',
        pitch_variants TEXT DEFAULT '[]',
        selected_pitch_index INTEGER DEFAULT 0,
        review_status TEXT DEFAULT 'pending',
        send_timestamp TEXT,
        created_at TEXT
    )
    """)
    
    # Campaigns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY,
        niche TEXT,
        platform TEXT,
        country TEXT,
        target_count INTEGER,
        status TEXT,
        leads_found INTEGER DEFAULT 0,
        leads_contactable INTEGER DEFAULT 0,
        emails_sent INTEGER DEFAULT 0,
        current_step TEXT DEFAULT '',
        progress_percentage INTEGER DEFAULT 0,
        logs TEXT DEFAULT '[]',
        created_at TEXT
    )
    """)
    
    # Sending Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sending_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        recipient_email TEXT,
        subject TEXT,
        body TEXT,
        status TEXT,
        error_message TEXT,
        timestamp TEXT,
        FOREIGN KEY(lead_id) REFERENCES leads(id)
    )
    """)
    
    # Suppression List (Never re-contact)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppression_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_or_domain TEXT UNIQUE,
        reason TEXT,
        created_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def save_lead(lead_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    pitch_json = json.dumps(lead_data.get("pitch_variants", []))
    now = datetime.utcnow().isoformat()
    
    try:
        cursor.execute("""
        INSERT INTO leads (
            domain, store_name, url, niche, platform, country, email, email_status,
            phone, instagram, linkedin, facebook, tiktok, founder_name,
            has_meta_pixel, has_ga4, has_tiktok_pixel, audit_notes,
            primary_opportunity, pitch_variants, selected_pitch_index,
            review_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET
            store_name=excluded.store_name,
            email=COALESCE(excluded.email, leads.email),
            email_status=COALESCE(excluded.email_status, leads.email_status),
            phone=COALESCE(excluded.phone, leads.phone),
            instagram=COALESCE(excluded.instagram, leads.instagram),
            linkedin=COALESCE(excluded.linkedin, leads.linkedin),
            has_meta_pixel=excluded.has_meta_pixel,
            has_ga4=excluded.has_ga4,
            has_tiktok_pixel=excluded.has_tiktok_pixel,
            audit_notes=excluded.audit_notes,
            primary_opportunity=excluded.primary_opportunity,
            pitch_variants=excluded.pitch_variants
        """, (
            lead_data.get("domain"),
            lead_data.get("store_name", ""),
            lead_data.get("url", ""),
            lead_data.get("niche", ""),
            lead_data.get("platform", "Shopify"),
            lead_data.get("country", "UK"),
            lead_data.get("email"),
            lead_data.get("email_status", "not_found"),
            lead_data.get("phone"),
            lead_data.get("instagram"),
            lead_data.get("linkedin"),
            lead_data.get("facebook"),
            lead_data.get("tiktok"),
            lead_data.get("founder_name"),
            1 if lead_data.get("has_meta_pixel") else 0,
            1 if lead_data.get("has_ga4") else 0,
            1 if lead_data.get("has_tiktok_pixel") else 0,
            lead_data.get("audit_notes", ""),
            lead_data.get("primary_opportunity", ""),
            pitch_json,
            lead_data.get("selected_pitch_index", 0),
            lead_data.get("review_status", "pending"),
            now
        ))
        conn.commit()
        lead_id = cursor.lastrowid
        conn.close()
        return lead_id
    except Exception as e:
        conn.close()
        print(f"Error saving lead: {e}")
        return -1

def get_all_leads(privacy_mode: bool = False, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM leads"
    params = []
    if filter_status and filter_status != "all":
        query += " WHERE review_status = ?"
        params.append(filter_status)
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    leads = []
    
    for row in rows:
        lead_dict = dict(row)
        lead_dict["has_meta_pixel"] = bool(lead_dict["has_meta_pixel"])
        lead_dict["has_ga4"] = bool(lead_dict["has_ga4"])
        lead_dict["has_tiktok_pixel"] = bool(lead_dict["has_tiktok_pixel"])
        try:
            lead_dict["pitch_variants"] = json.loads(lead_dict["pitch_variants"])
        except Exception:
            lead_dict["pitch_variants"] = []
            
        if privacy_mode:
            if lead_dict.get("email"):
                parts = lead_dict["email"].split("@")
                if len(parts) == 2:
                    lead_dict["email"] = f"{parts[0][:2]}***@{parts[1]}"
            if lead_dict.get("phone"):
                lead_dict["phone"] = lead_dict["phone"][:4] + "****" + lead_dict["phone"][-2:] if len(lead_dict["phone"]) > 6 else "***"
        leads.append(lead_dict)
        
    conn.close()
    return leads

def get_lead_by_id(lead_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    lead_dict = dict(row)
    lead_dict["has_meta_pixel"] = bool(lead_dict["has_meta_pixel"])
    lead_dict["has_ga4"] = bool(lead_dict["has_ga4"])
    lead_dict["has_tiktok_pixel"] = bool(lead_dict["has_tiktok_pixel"])
    try:
        lead_dict["pitch_variants"] = json.loads(lead_dict["pitch_variants"])
    except Exception:
        lead_dict["pitch_variants"] = []
    return lead_dict

def update_lead_status(lead_id: int, status: str, selected_pitch: Optional[int] = None, custom_variants: Optional[List[Dict[str, Any]]] = None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() if status == "sent" else None
    
    if custom_variants is not None and selected_pitch is not None:
        cursor.execute("""
        UPDATE leads 
        SET review_status = ?, selected_pitch_index = ?, pitch_variants = ?, send_timestamp = COALESCE(?, send_timestamp)
        WHERE id = ?
        """, (status, selected_pitch, json.dumps(custom_variants), now, lead_id))
    elif selected_pitch is not None:
        cursor.execute("""
        UPDATE leads 
        SET review_status = ?, selected_pitch_index = ?, send_timestamp = COALESCE(?, send_timestamp)
        WHERE id = ?
        """, (status, selected_pitch, now, lead_id))
    else:
        cursor.execute("""
        UPDATE leads 
        SET review_status = ?, send_timestamp = COALESCE(?, send_timestamp)
        WHERE id = ?
        """, (status, now, lead_id))
        
    conn.commit()
    conn.close()

def log_email_send(lead_id: int, recipient_email: str, subject: str, body: str, status: str, error_message: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sending_logs (lead_id, recipient_email, subject, body, status, error_message, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lead_id, recipient_email, subject, body, status, error_message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
    deliverable_emails = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE has_meta_pixel = 0")
    pixel_leaks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE review_status = 'approved'")
    approved_queue = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE review_status = 'sent'")
    sent_emails = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_leads": total_leads,
        "deliverable_emails": deliverable_emails,
        "pixel_leaks": pixel_leaks,
        "approved_queue": approved_queue,
        "sent_emails": sent_emails
    }
