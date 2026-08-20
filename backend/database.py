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
    
    # Base Leads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        store_name TEXT,
        url TEXT,
        niche TEXT,
        platform TEXT,
        country TEXT,
        est_monthly_revenue TEXT DEFAULT '$10k-$50k',
        lead_score INTEGER DEFAULT 50,
        lead_tier TEXT DEFAULT 'Silver',
        founder_name TEXT,
        founder_title TEXT DEFAULT 'Founder & Owner',
        email TEXT,
        email_status TEXT DEFAULT 'not_found',
        phone TEXT,
        instagram TEXT,
        linkedin TEXT,
        facebook TEXT,
        tiktok TEXT,
        reddit_username TEXT,
        has_google_ads INTEGER DEFAULT 0,
        has_meta_pixel INTEGER DEFAULT 0,
        has_ga4 INTEGER DEFAULT 0,
        has_tiktok_pixel INTEGER DEFAULT 0,
        has_active_meta_ads INTEGER DEFAULT 0,
        active_ad_count INTEGER DEFAULT 0,
        audit_notes TEXT DEFAULT '',
        primary_opportunity TEXT DEFAULT '',
        pitch_variants TEXT DEFAULT '[]',
        multi_channel_pitches TEXT DEFAULT '{}',
        selected_pitch_index INTEGER DEFAULT 0,
        review_status TEXT DEFAULT 'pending',
        tags TEXT DEFAULT '[]',
        send_timestamp TEXT,
        created_at TEXT
    )
    """)

    # Check and migrate any missing columns in existing SQLite DB
    cursor.execute("PRAGMA table_info(leads)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    
    migrations = [
        ("est_monthly_revenue", "TEXT DEFAULT '$10k-$50k'"),
        ("lead_score", "INTEGER DEFAULT 50"),
        ("lead_tier", "TEXT DEFAULT 'Silver'"),
        ("founder_title", "TEXT DEFAULT 'Founder & Owner'"),
        ("reddit_username", "TEXT"),
        ("has_google_ads", "INTEGER DEFAULT 0"),
        ("has_active_meta_ads", "INTEGER DEFAULT 0"),
        ("active_ad_count", "INTEGER DEFAULT 0"),
        ("multi_channel_pitches", "TEXT DEFAULT '{}'"),
        ("tags", "TEXT DEFAULT '[]'")
    ]
    for col_name, col_def in migrations:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}")
            except Exception as e:
                print(f"Migration note ({col_name}): {e}")

    # Create FTS5 Virtual Table for ultra-fast instant searches (if supported)
    try:
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS leads_fts USING fts5(
            domain, store_name, niche, founder_name, email, primary_opportunity, tags,
            content='leads', content_rowid='id'
        )
        """)
        
        # FTS Triggers for sync
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS leads_ai AFTER INSERT ON leads BEGIN
            INSERT INTO leads_fts(rowid, domain, store_name, niche, founder_name, email, primary_opportunity, tags)
            VALUES (new.id, new.domain, new.store_name, new.niche, new.founder_name, new.email, new.primary_opportunity, new.tags);
        END;
        """)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS leads_ad AFTER DELETE ON leads BEGIN
            INSERT INTO leads_fts(leads_fts, rowid, domain, store_name, niche, founder_name, email, primary_opportunity, tags)
            VALUES('delete', old.id, old.domain, old.store_name, old.niche, old.founder_name, old.email, old.primary_opportunity, old.tags);
        END;
        """)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS leads_au AFTER UPDATE ON leads BEGIN
            INSERT INTO leads_fts(leads_fts, rowid, domain, store_name, niche, founder_name, email, primary_opportunity, tags)
            VALUES('delete', old.id, old.domain, old.store_name, old.niche, old.founder_name, old.email, old.primary_opportunity, old.tags);
            INSERT INTO leads_fts(rowid, domain, store_name, niche, founder_name, email, primary_opportunity, tags)
            VALUES (new.id, new.domain, new.store_name, new.niche, new.founder_name, new.email, new.primary_opportunity, new.tags);
        END;
        """)
    except Exception as e:
        print(f"FTS5 initialization note (fallback will be used): {e}")
    
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

def _format_lead_row(row_dict: Dict[str, Any], privacy_mode: bool = False) -> Dict[str, Any]:
    row_dict["has_google_ads"] = bool(row_dict.get("has_google_ads", 0))
    row_dict["has_meta_pixel"] = bool(row_dict.get("has_meta_pixel", 0))
    row_dict["has_ga4"] = bool(row_dict.get("has_ga4", 0))
    row_dict["has_tiktok_pixel"] = bool(row_dict.get("has_tiktok_pixel", 0))
    row_dict["has_active_meta_ads"] = bool(row_dict.get("has_active_meta_ads", 0))
    
    try:
        row_dict["pitch_variants"] = json.loads(row_dict.get("pitch_variants", "[]") or "[]")
    except Exception:
        row_dict["pitch_variants"] = []
        
    try:
        row_dict["multi_channel_pitches"] = json.loads(row_dict.get("multi_channel_pitches", "{}") or "{}")
    except Exception:
        row_dict["multi_channel_pitches"] = {}
        
    try:
        row_dict["tags"] = json.loads(row_dict.get("tags", "[]") or "[]")
    except Exception:
        row_dict["tags"] = []

    if privacy_mode:
        if row_dict.get("email"):
            parts = row_dict["email"].split("@")
            if len(parts) == 2:
                row_dict["email"] = f"{parts[0][:2]}***@{parts[1]}"
        if row_dict.get("phone"):
            p = row_dict["phone"]
            row_dict["phone"] = p[:4] + "****" + p[-2:] if len(p) > 6 else "***"
            
    return row_dict

def save_lead(lead_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    pitch_json = json.dumps(lead_data.get("pitch_variants", []))
    multi_pitch_json = json.dumps(lead_data.get("multi_channel_pitches", {}))
    tags_json = json.dumps(lead_data.get("tags", []))
    now = datetime.utcnow().isoformat()
    
    try:
        cursor.execute("""
        INSERT INTO leads (
            domain, store_name, url, niche, platform, country,
            est_monthly_revenue, lead_score, lead_tier,
            founder_name, founder_title,
            email, email_status, phone,
            instagram, linkedin, facebook, tiktok, reddit_username,
            has_google_ads, has_meta_pixel, has_ga4, has_tiktok_pixel,
            has_active_meta_ads, active_ad_count,
            audit_notes, primary_opportunity,
            pitch_variants, multi_channel_pitches, selected_pitch_index,
            review_status, tags, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET
            store_name=excluded.store_name,
            est_monthly_revenue=COALESCE(excluded.est_monthly_revenue, leads.est_monthly_revenue),
            lead_score=COALESCE(excluded.lead_score, leads.lead_score),
            lead_tier=COALESCE(excluded.lead_tier, leads.lead_tier),
            founder_name=COALESCE(excluded.founder_name, leads.founder_name),
            founder_title=COALESCE(excluded.founder_title, leads.founder_title),
            email=COALESCE(excluded.email, leads.email),
            email_status=COALESCE(excluded.email_status, leads.email_status),
            phone=COALESCE(excluded.phone, leads.phone),
            instagram=COALESCE(excluded.instagram, leads.instagram),
            linkedin=COALESCE(excluded.linkedin, leads.linkedin),
            facebook=COALESCE(excluded.facebook, leads.facebook),
            tiktok=COALESCE(excluded.tiktok, leads.tiktok),
            reddit_username=COALESCE(excluded.reddit_username, leads.reddit_username),
            has_google_ads=excluded.has_google_ads,
            has_meta_pixel=excluded.has_meta_pixel,
            has_ga4=excluded.has_ga4,
            has_tiktok_pixel=excluded.has_tiktok_pixel,
            has_active_meta_ads=excluded.has_active_meta_ads,
            active_ad_count=excluded.active_ad_count,
            audit_notes=excluded.audit_notes,
            primary_opportunity=excluded.primary_opportunity,
            pitch_variants=excluded.pitch_variants,
            multi_channel_pitches=COALESCE(excluded.multi_channel_pitches, leads.multi_channel_pitches),
            tags=COALESCE(excluded.tags, leads.tags)
        """, (
            lead_data.get("domain"),
            lead_data.get("store_name", ""),
            lead_data.get("url", ""),
            lead_data.get("niche", ""),
            lead_data.get("platform", "Shopify"),
            lead_data.get("country", "UK"),
            lead_data.get("est_monthly_revenue", "$10k-$50k"),
            int(lead_data.get("lead_score", 50)),
            lead_data.get("lead_tier", "Silver"),
            lead_data.get("founder_name"),
            lead_data.get("founder_title", "Founder & Owner"),
            lead_data.get("email"),
            lead_data.get("email_status", "not_found"),
            lead_data.get("phone"),
            lead_data.get("instagram"),
            lead_data.get("linkedin"),
            lead_data.get("facebook"),
            lead_data.get("tiktok"),
            lead_data.get("reddit_username"),
            1 if lead_data.get("has_google_ads") else 0,
            1 if lead_data.get("has_meta_pixel") else 0,
            1 if lead_data.get("has_ga4") else 0,
            1 if lead_data.get("has_tiktok_pixel") else 0,
            1 if lead_data.get("has_active_meta_ads") else 0,
            int(lead_data.get("active_ad_count", 0)),
            lead_data.get("audit_notes", ""),
            lead_data.get("primary_opportunity", ""),
            pitch_json,
            multi_pitch_json,
            lead_data.get("selected_pitch_index", 0),
            lead_data.get("review_status", "pending"),
            tags_json,
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
        if filter_status == "pixel_leaks":
            query += " WHERE has_meta_pixel = 0"
        elif filter_status == "google_ads_gaps":
            query += " WHERE has_google_ads = 0"
        elif filter_status == "ready_for_review":
            query += " WHERE email IS NOT NULL AND email != '' AND review_status = 'pending'"
        else:
            query += " WHERE review_status = ?"
            params.append(filter_status)
    query += " ORDER BY lead_score DESC, id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    leads = [_format_lead_row(dict(row), privacy_mode) for row in rows]
    conn.close()
    return leads

def search_leads(
    query_text: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    value_tier: Optional[str] = None,
    has_google_ads: Optional[bool] = None,
    has_meta_pixel: Optional[bool] = None,
    channel: Optional[str] = None,
    niche: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "lead_score",
    sort_order: str = "DESC",
    privacy_mode: bool = False
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    # 1. Text Search across store name, domain, founder, niche, opportunity, tags
    if query_text and query_text.strip():
        q = f"%{query_text.strip()}%"
        conditions.append("""(
            domain LIKE ? OR store_name LIKE ? OR founder_name LIKE ? 
            OR niche LIKE ? OR primary_opportunity LIKE ? OR tags LIKE ? OR est_monthly_revenue LIKE ?
        )""")
        params.extend([q, q, q, q, q, q, q])
        
    # 2. Score Range Filter
    if min_score is not None:
        conditions.append("lead_score >= ?")
        params.append(min_score)
    if max_score is not None:
        conditions.append("lead_score <= ?")
        params.append(max_score)
        
    # 3. Value / Revenue Tier
    if value_tier and value_tier != "all":
        conditions.append("est_monthly_revenue = ?")
        params.append(value_tier)
        
    # 4. Tech Audit Flags
    if has_google_ads is not None:
        conditions.append("has_google_ads = ?")
        params.append(1 if has_google_ads else 0)
    if has_meta_pixel is not None:
        conditions.append("has_meta_pixel = ?")
        params.append(1 if has_meta_pixel else 0)
        
    # 5. Channel Availability Filter
    if channel and channel != "all":
        if channel == "email":
            conditions.append("email IS NOT NULL AND email != ''")
        elif channel == "linkedin":
            conditions.append("linkedin IS NOT NULL AND linkedin != ''")
        elif channel == "instagram":
            conditions.append("instagram IS NOT NULL AND instagram != ''")
        elif channel == "reddit":
            conditions.append("reddit_username IS NOT NULL AND reddit_username != ''")
        elif channel == "facebook":
            conditions.append("facebook IS NOT NULL AND facebook != ''")
            
    # 6. Niche and Country
    if niche and niche != "all":
        conditions.append("niche LIKE ?")
        params.append(f"%{niche}%")
    if country and country != "all":
        conditions.append("country = ?")
        params.append(country)
        
    # 7. Review Status
    if status and status != "all":
        if status == "ready_for_review":
            conditions.append("email IS NOT NULL AND email != '' AND review_status = 'pending'")
        elif status == "pixel_leaks":
            conditions.append("has_meta_pixel = 0")
        elif status == "google_ads_gaps":
            conditions.append("has_google_ads = 0")
        else:
            conditions.append("review_status = ?")
            params.append(status)
            
    # Build SQL
    sql = "SELECT * FROM leads"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
        
    # Sanitized Sort Column
    valid_sorts = {
        "id": "id",
        "lead_score": "lead_score",
        "store_name": "store_name",
        "est_monthly_revenue": "est_monthly_revenue",
        "created_at": "created_at"
    }
    sort_col = valid_sorts.get(sort_by, "lead_score")
    sort_dir = "ASC" if sort_order.upper() == "ASC" else "DESC"
    sql += f" ORDER BY {sort_col} {sort_dir}, id DESC"
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    leads = [_format_lead_row(dict(row), privacy_mode) for row in rows]
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
    return _format_lead_row(dict(row))

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

def update_lead_tags(lead_id: int, tags: List[str]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET tags = ? WHERE id = ?", (json.dumps(tags), lead_id))
    conn.commit()
    conn.close()

def delete_lead(lead_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    cursor.execute("DELETE FROM sending_logs WHERE lead_id = ?", (lead_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def prune_invalid_leads() -> int:
    """Removes agency, blog, SaaS, or dummy placeholder entries from database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    junk_domains = [
        "analyzify.com", "skailama.com", "builtwith.com", "suttoncommerce.co.uk",
        "glazedigital.com", "findniche.com", "theshitbot.com", "skool.com",
        "sellercenter.io", "huptechweb.com", "getclipara.com", "magenest.com",
        "shopify.com", "dickssportinggoods.com", "amazon.com", "ebay.com"
    ]
    
    placeholders = ",".join(["?"] * len(junk_domains))
    cursor.execute(f"DELETE FROM leads WHERE domain IN ({placeholders}) OR domain LIKE '%.dev' OR domain LIKE '%.app' OR domain LIKE '%shopify.dev%'", junk_domains)
    deleted_count = cursor.rowcount
    
    cursor.execute("""
    UPDATE leads 
    SET email = NULL, email_status = 'not_found'
    WHERE email LIKE '%xxx@%' 
       OR email LIKE 'blocked@%' 
       OR email LIKE 'test@%' 
       OR email LIKE '%@shopify.com' 
       OR email LIKE '%@sentry.io'
    """)
    
    conn.commit()
    conn.close()
    return deleted_count

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
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE has_google_ads = 0")
    google_ads_gaps = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE review_status = 'approved'")
    approved_queue = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE review_status = 'sent'")
    sent_emails = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE linkedin IS NOT NULL AND linkedin != ''")
    linkedin_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE instagram IS NOT NULL AND instagram != ''")
    instagram_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_score >= 70")
    hot_leads = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_leads": total_leads,
        "deliverable_emails": deliverable_emails,
        "pixel_leaks": pixel_leaks,
        "google_ads_gaps": google_ads_gaps,
        "approved_queue": approved_queue,
        "sent_emails": sent_emails,
        "linkedin_leads": linkedin_leads,
        "instagram_leads": instagram_leads,
        "hot_leads": hot_leads
    }

