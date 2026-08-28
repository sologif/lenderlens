import json
from fastapi import APIRouter
from database import get_db_connection

router = APIRouter(prefix="/api", tags=["Demo & Stats"])

@router.get("/demo/scenarios")
def get_demo_scenarios():
    """
    Returns the three benchmark test scenarios:
    🟢 Legitimate: ABC Finance (Risk ~18, Govt Match: True, Website Match: True, Low GNN/LSTM)
    🟡 Uncertain: QuickLoan (Risk ~56, Govt Record: True, Website Match: Inconclusive, Needs Review)
    🔴 Fraudulent: FastCash (Risk ~91, Identity Mismatch, Advance Fee, High GNN/LSTM, Block)
    """
    return [
        {
            "id": "scenario_legitimate",
            "name": "ABC Finance",
            "badge": "🟢 Legitimate",
            "expected_risk": "LOW (18/100)",
            "expected_decision": "ALLOW",
            "domain": "abcfinance.com",
            "claimed_lender": "ABC Finance Ltd.",
            "url": "/demo/legitimate/index.html",
            "key_traits": [
                "Official RBI NBFC Registry record matches perfectly",
                "Domain abcfinance.com verified with SSL & MCA listing",
                "Full Key Fact Statement (KFS) provided with 14.5% APR",
                "No advance fees or abusive device permissions",
                "Clean, isolated network graph"
            ]
        },
        {
            "id": "scenario_uncertain",
            "name": "QuickLoan Financial",
            "badge": "🟡 Uncertain / Needs Review",
            "expected_risk": "UNCERTAIN (48-56/100)",
            "expected_decision": "HUMAN_REVIEW",
            "domain": "quickloan-app.in",
            "claimed_lender": "QuickLoan Financial Services Ltd.",
            "url": "/demo/uncertain/index.html",
            "key_traits": [
                "Valid RBI registration found under legal entity, but unofficial domain alias used",
                "Incomplete Key Fact Statement disclosure",
                "Requests Contacts permission for KYC references",
                "Moderate elevation in recent inquiry trend",
                "Requires Human-in-the-Loop Analyst Verification"
            ]
        },
        {
            "id": "scenario_fraudulent",
            "name": "FastCash Instant Loans",
            "badge": "🔴 Fraudulent / Scam",
            "expected_risk": "HIGH (91-96/100)",
            "expected_decision": "BLOCK",
            "domain": "fastcash-instantloans.net",
            "claimed_lender": "ABC Finance Ltd.",
            "url": "/demo/fraudulent/index.html",
            "key_traits": [
                "Impersonates licensed NBFC ABC Finance Ltd.",
                "Website mismatch: Claimed 'ABC Finance' on rogue domain fastcash-instantloans.net",
                "Advance fee: Demands ₹1,500 security deposit prior to disbursement",
                "Connected to 3 flagged phishing domains & 2 mule UPI accounts in GNN",
                "Abnormal LSTM burst (+1840% grievance volume surge)"
            ]
        }
    ]

@router.get("/stats")
def get_dashboard_stats():
    """Aggregates high-level metrics for the Analyst Dashboard Overview."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_cases = cursor.execute("SELECT COUNT(*) as c FROM cases").fetchone()["c"]
    high_risk_count = cursor.execute("SELECT COUNT(*) as c FROM cases WHERE risk_level IN ('HIGH', 'CRITICAL')").fetchone()["c"]
    pending_count = cursor.execute("SELECT COUNT(*) as c FROM cases WHERE status = 'PENDING'").fetchone()["c"]
    reviewed_count = cursor.execute("SELECT COUNT(*) as c FROM cases WHERE status = 'REVIEWED'").fetchone()["c"]
    total_reports = cursor.execute("SELECT COUNT(*) as c FROM user_reports").fetchone()["c"]

    # Recent cases
    recent_rows = cursor.execute("SELECT * FROM cases ORDER BY created_at DESC LIMIT 6").fetchall()
    recent_cases = []
    for r in recent_rows:
        reasons = []
        try:
            reasons = json.loads(r["reasons_json"])
        except:
            pass
        recent_cases.append({
            "id": r["id"],
            "claimed_name": r["claimed_name"],
            "domain": r["domain"],
            "risk_score": r["risk_score"],
            "risk_level": r["risk_level"],
            "decision": r["decision"],
            "status": r["status"],
            "analyst_action": r["analyst_action"],
            "created_at": r["created_at"],
            "reasons": reasons[:2]
        })

    conn.close()

    low_count = max(total_cases - high_risk_count - pending_count, 1)

    return {
        "total_cases": total_cases,
        "high_risk_count": high_risk_count,
        "pending_count": pending_count,
        "reviewed_count": reviewed_count,
        "total_reports": total_reports,
        "recent_cases": recent_cases,
        "risk_trend": [
            {"date": "Day 1", "low": 18, "uncertain": 4, "high": 2},
            {"date": "Day 2", "low": 24, "uncertain": 6, "high": 5},
            {"date": "Day 3", "low": 29, "uncertain": 5, "high": 8},
            {"date": "Day 4", "low": 35, "uncertain": 8, "high": 12},
            {"date": "Day 5", "low": 42, "uncertain": 10, "high": 18},
            {"date": "Day 6", "low": 50, "uncertain": 12, "high": 24},
            {"date": "Today", "low": low_count, "uncertain": pending_count, "high": high_risk_count}
        ]
    }
