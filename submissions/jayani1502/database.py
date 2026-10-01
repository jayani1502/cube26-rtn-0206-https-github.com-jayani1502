import os
import json
import sqlite3
from typing import List, Dict, Any
from config import DB_PATH, logger


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            predicted_disposition TEXT NOT NULL,
            ground_truth_disposition TEXT,
            overall_confidence TEXT NOT NULL,
            identity_verdict TEXT NOT NULL,
            completeness_verdict TEXT NOT NULL,
            raw_payload TEXT NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")


def save_audit_entry(record_id: str, order_id: str, sku: str, predicted_disposition: str, ground_truth: str, confidence: str, identity_verdict: str, completeness_verdict: str, raw_payload: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (record_id, order_id, sku, predicted_disposition, ground_truth_disposition, overall_confidence, identity_verdict, completeness_verdict, raw_payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (record_id, order_id, sku, predicted_disposition, ground_truth, confidence, identity_verdict, completeness_verdict, json.dumps(raw_payload)))
    conn.commit()
    conn.close()


def fetch_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM audit_logs ORDER BY executed_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
