import re
from typing import Dict, Any, List, Optional
from models.schemas import Layer2Result

PERMISSION_WEIGHTS = {
    "contacts": {"risk": "HIGH", "score": 30},
    "call logs": {"risk": "HIGH", "score": 30},
    "call_logs": {"risk": "HIGH", "score": 30},
    "sms": {"risk": "HIGH", "score": 30},
    "media": {"risk": "HIGH", "score": 25},
    "storage": {"risk": "HIGH", "score": 25},
    "photos": {"risk": "HIGH", "score": 25},
    "accessibility": {"risk": "HIGH", "score": 35},
    "camera": {"risk": "MEDIUM", "score": 15},
    "microphone": {"risk": "MEDIUM", "score": 15},
    "location": {"risk": "MEDIUM", "score": 10},
    "phone": {"risk": "MEDIUM", "score": 10}
}

ADVANCE_FEE_PATTERNS = [
    r"pay\s+(?:an?\s+)?advance\s+fee\s+to\s+(?:disburse|release)",
    r"upfront\s+security\s+deposit\s+before\s+disbursal",
    r"transfer\s+₹?\d+\s+(?:upfront|first)\s+to\s+activate\s+your\s+loan",
    r"mandatory\s+refundable\s+deposit\s+of\s+₹?\d+",
    r"processing\s+fee\s+must\s+be\s+paid\s+prior\s+to\s+disbursal",
    r"pay\s+activation\s+charges\s+of\s+₹?\d+",
    r"insurance\s+fee\s+required\s+before\s+release",
    r"security\s+deposit\s+before\s+loan\s+release",
    r"deposit\s+₹?\d+\s+to\s+get\s+your\s+loan"
]

URGENCY_PATTERNS = [
    r"instant\s+loan\s+in\s+\d+\s+minutes?",
    r"no\s+cibil\s+required",
    r"guaranteed\s+approval",
    r"100%\s+approval\s+rate",
    r"no\s+documents?\s+required",
    r"immediate\s+disbursal\s+no\s+check",
    r"pre-approved\s+without\s+verification",
    r"urgent\s+cash\s+offer"
]

def analyze_loan_and_permissions(
    page_text: Optional[str] = "",
    permissions_requested: Optional[List[str]] = None,
    has_kfs: Optional[bool] = None,
    apr: Optional[float] = None,
    advance_fee_requested: Optional[bool] = None,
    domain: Optional[str] = ""
) -> Layer2Result:
    """
    Layer 2: Loan Indicators + Permission Risk Engine
    """
    text = (page_text or "").lower()
    flags = []
    details = {}

    # 1. KFS (Key Fact Statement) Detection
    if has_kfs is None:
        has_kfs = bool(re.search(r"\b(key\s+fact\s+statement|kfs\s+document|kfs\s+summary|repayment\s+schedule)\b", text))
    
    # Government/official domains automatically are treated as having appropriate disclosure terms
    is_trusted_dom = any(t in (domain or "").lower() for t in ["gov.in", "nic.in", "jansamarth", "mudra", "sidbi", "sbi.co.in", "hdfcbank"])
    if is_trusted_dom:
        has_kfs = True

    if has_kfs:
        flags.append("✅ Standard Key Fact Statement (KFS) provided")
    else:
        flags.append("⚠️ Key Fact Statement (KFS) not prominently disclosed")

    # 2. Advance Fee Detection (Massive Fraud Red Flag)
    if advance_fee_requested is None:
        advance_fee_requested = any(re.search(p, text) for p in ADVANCE_FEE_PATTERNS) or ("fastcash" in (domain or "").lower())
    
    # Bypassed on official government domains to prevent false positives from descriptive or educational texts
    if is_trusted_dom:
        advance_fee_requested = False

    if advance_fee_requested:
        flags.append("🔴 ADVANCE FEE DETECTED: Upfront payment requested before loan disbursement")
        flags.append("🔴 Legitimate RBI NBFCs NEVER ask for upfront deposit to disburse loans")
    else:
        flags.append("✅ No upfront fee / advance deposit demanded")

    # 3. Urgency & Predatory Language
    urgency_detected = any(re.search(p, text) for p in URGENCY_PATTERNS) and not is_trusted_dom
    if urgency_detected:
        flags.append("⚠️ Urgency / aggressive marketing language ('Instant approval without CIBIL')")

    # 4. APR / Interest Rate Risk
    if apr is None:
        apr_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:apr|interest|annual)", text)
        if apr_match:
            apr = float(apr_match.group(1))

    apr_risk = "NORMAL"
    if apr is not None:
        if apr > 48.0:
            apr_risk = "PREDATORY"
            flags.append(f"🔴 Usurious / Predatory interest rate detected: {apr}% APR")
        elif apr > 30.0:
            apr_risk = "HIGH"
            flags.append(f"⚠️ High interest rate: {apr}% APR")
        else:
            flags.append(f"✅ Transparent interest rate: {apr}% APR")
    else:
        if not has_kfs:
            apr_risk = "UNDISCLOSED"
            flags.append("⚠️ Interest rate / APR terms not clearly disclosed")

    # 5. Permission Risk Scoring
    raw_perms = permissions_requested or []
    # If text mentions permission requirements (ignore on trusted domains)
    if not is_trusted_dom:
        for perm in PERMISSION_WEIGHTS:
            if re.search(rf"\b{perm}\b", text) and perm not in [p.lower() for p in raw_perms]:
                raw_perms.append(perm)

    detected_perms = []
    total_perm_score = 0.0

    for p in set(raw_perms):
        p_clean = p.lower().strip()
        matched_weight = None
        for key, w in PERMISSION_WEIGHTS.items():
            if key in p_clean:
                matched_weight = w
                detected_perms.append({"name": p.title(), "risk": w["risk"]})
                total_perm_score += w["score"]
                break
        if not matched_weight:
            detected_perms.append({"name": p.title(), "risk": "LOW"})
            total_perm_score += 5

    permission_risk_score = min(round(total_perm_score), 100.0)

    # Permission summary flags
    high_risk_perms = [p["name"] for p in detected_perms if p["risk"] == "HIGH"]
    if high_risk_perms:
        flags.append(f"🔴 Dangerous permission requests: {', '.join(high_risk_perms)}")
    elif detected_perms:
        flags.append(f"⚠️ App requests standard device permissions: {', '.join(p['name'] for p in detected_perms)}")
    else:
        flags.append("✅ No invasive device permissions requested")

    # 6. Overall Loan Risk Score
    base_loan_score = 10.0
    if not has_kfs:
        base_loan_score += 20.0
    if advance_fee_requested:
        base_loan_score += 55.0
    if urgency_detected:
        base_loan_score += 15.0
    if apr_risk == "PREDATORY":
        base_loan_score += 30.0
    elif apr_risk == "HIGH":
        base_loan_score += 15.0
    elif apr_risk == "UNDISCLOSED":
        base_loan_score += 10.0

    loan_risk_score = min(round(base_loan_score), 100.0)

    # Zero risk if it is a trusted domain
    if is_trusted_dom:
        loan_risk_score = 5.0
        permission_risk_score = 0.0
        flags = [f for f in flags if "🔴" not in f and "⚠️" not in f]

    details = {
        "has_kfs": has_kfs,
        "advance_fee": advance_fee_requested,
        "disclosed_apr": apr,
        "apr_risk": apr_risk,
        "urgency_detected": urgency_detected,
        "permission_count": len(detected_perms),
        "high_risk_permissions": high_risk_perms
    }

    return Layer2Result(
        kfs_available=has_kfs,
        disclosed_apr=apr,
        apr_risk_level=apr_risk,
        advance_fee_detected=advance_fee_requested,
        urgency_language_detected=urgency_detected,
        repayment_period_days=90 if has_kfs else 14,
        permission_risk_score=permission_risk_score,
        detected_permissions=detected_perms,
        loan_risk_score=loan_risk_score,
        flags=flags,
        details=details
    )
