import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from database import get_db_connection
from models.schemas import CaseReviewRequest, UserReportRequest

router = APIRouter(prefix="/api/cases", tags=["Cases"])

@router.get("")
def list_cases(status: str = None, risk_level: str = None):
    """Lists all investigated cases for the Analyst Dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM cases WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status.upper())
    if risk_level:
        query += " AND risk_level = ?"
        params.append(risk_level.upper())

    query += " ORDER BY created_at DESC"
    rows = cursor.execute(query, params).fetchall()
    conn.close()

    cases = []
    for r in rows:
        reasons = []
        try:
            reasons = json.loads(r["reasons_json"])
        except:
            pass

        cases.append({
            "id": r["id"],
            "lender_id": r["lender_id"],
            "claimed_name": r["claimed_name"],
            "domain": r["domain"],
            "url": r["url"],
            "risk_score": r["risk_score"],
            "risk_level": r["risk_level"],
            "decision": r["decision"],
            "confidence": r["confidence"],
            "reasons": reasons,
            "status": r["status"],
            "analyst_action": r["analyst_action"],
            "analyst_notes": r["analyst_notes"],
            "analyst_id": r["analyst_id"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"]
        })

    return cases

@router.get("/{case_id}")
def get_case_detail(case_id: str):
    """Retrieves full case details including all 4 evidence layer breakdowns, GNN subgraph, and LSTM sequence."""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Case not found")

    reasons = []
    evidence = {}
    try:
        reasons = json.loads(row["reasons_json"])
        evidence = json.loads(row["evidence_json"])
    except:
        pass

    return {
        "id": row["id"],
        "lender_id": row["lender_id"],
        "claimed_name": row["claimed_name"],
        "domain": row["domain"],
        "url": row["url"],
        "risk_score": row["risk_score"],
        "risk_level": row["risk_level"],
        "decision": row["decision"],
        "confidence": row["confidence"],
        "reasons": reasons,
        "evidence": evidence,
        "status": row["status"],
        "analyst_action": row["analyst_action"],
        "analyst_notes": row["analyst_notes"],
        "analyst_id": row["analyst_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@router.post("/{case_id}/review")
def review_case(case_id: str, req: CaseReviewRequest):
    """Human-in-the-loop: Analyst records decision (APPROVE, WARN, BLOCK, ESCALATE) and notes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE cases 
    SET status = 'REVIEWED',
        analyst_action = ?,
        analyst_notes = ?,
        analyst_id = ?,
        updated_at = ?
    WHERE id = ?;
    """, (req.action.upper(), req.analyst_notes, req.analyst_id, now_str, case_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Case not found")

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "case_id": case_id,
        "action": req.action.upper(),
        "analyst_notes": req.analyst_notes,
        "reviewed_at": now_str
    }

@router.post("/report")
def submit_user_report(req: UserReportRequest):
    """Records user-submitted fraud reports from the Chrome extension or dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO user_reports (url, domain, lender_name, reason, details, created_at)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (req.url, req.domain, req.lender_name, req.reason, req.details, now_str))

    conn.commit()
    conn.close()

    return {"status": "reported", "timestamp": now_str}
