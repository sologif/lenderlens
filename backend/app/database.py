import sqlite3
import json
import os
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "lenderlens.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Government / Regulatory Reference Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS government_registry (
        lender_id TEXT PRIMARY KEY,
        legal_name TEXT NOT NULL,
        registration_number TEXT NOT NULL,
        status TEXT NOT NULL,
        official_domain TEXT NOT NULL,
        official_phone TEXT,
        registration_date TEXT,
        regulator TEXT NOT NULL
    );
    """)

    # 2. Graph Nodes (Entities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS graph_nodes (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL, -- LENDER, DOMAIN, PHONE, EMAIL, APP, PAYMENT_ACCOUNT, UPI_ID, BANK_ACCOUNT
        entity_value TEXT NOT NULL,
        label TEXT NOT NULL,
        is_suspicious INTEGER DEFAULT 0,
        risk_score REAL DEFAULT 0,
        metadata TEXT
    );
    """)

    # 3. Graph Edges (Relationships)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS graph_edges (
        id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        relation_type TEXT NOT NULL, -- USES, OWNS, CONNECTED_TO, REGISTERED_AS, PAYS_TO, SHARES_PHONE, SHARES_DOMAIN, SHARES_ACCOUNT
        is_suspicious INTEGER DEFAULT 0,
        FOREIGN KEY (source_id) REFERENCES graph_nodes(id),
        FOREIGN KEY (target_id) REFERENCES graph_nodes(id)
    );
    """)

    # 4. Temporal Activities (Historical sequences for LSTM)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS temporal_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        activity_type TEXT NOT NULL, -- COMPLAINTS, INQUIRIES, PAYMENT_REQUESTS, TRAFFIC_SPIKE
        activity_value REAL NOT NULL
    );
    """)

    # 5. Cases (Human-in-the-Loop)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        lender_id TEXT,
        claimed_name TEXT NOT NULL,
        domain TEXT NOT NULL,
        url TEXT NOT NULL,
        risk_score REAL NOT NULL,
        risk_level TEXT NOT NULL, -- LOW, UNCERTAIN, HIGH, CRITICAL
        decision TEXT NOT NULL,   -- ALLOW, HUMAN_REVIEW, WARN, BLOCK
        confidence REAL NOT NULL,
        reasons_json TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING', -- PENDING, REVIEWED
        analyst_action TEXT DEFAULT NULL, -- APPROVE, WARN, BLOCK, ESCALATE
        analyst_notes TEXT DEFAULT '',
        analyst_id TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 6. User Reports
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        domain TEXT NOT NULL,
        lender_name TEXT,
        reason TEXT,
        details TEXT,
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
