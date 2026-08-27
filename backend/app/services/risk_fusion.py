from typing import Dict, Any, List, Optional
from config import (
    RiskWeights, DEFAULT_WEIGHTS,
    LOW_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD, HIGH_RISK_THRESHOLD,
    PROTOTYPE_DISCLAIMER
)
from models.schemas import (
    Layer1Result, Layer2Result, Layer3Result, Layer4Result, RiskFusionResult
)

def fuse_risk_scores(
    layer1: Layer1Result,
    layer2: Layer2Result,
    layer3: Layer3Result,
    layer4: Layer4Result,
    weights: Optional[RiskWeights] = None
) -> RiskFusionResult:
    """
    Risk Fusion Engine combining parallel evidence sources:
    - Layer 1: Identity & Regulatory Mismatch
    - Layer 2: Loan indicators & Permission Risk
    - Layer 3: LSTM Temporal Behavioral Risk
    - Layer 4: GNN Graph Network Risk
    """
    w = weights or DEFAULT_WEIGHTS

    weighted_score = (
        layer1.identity_consistency_score * w.identity_weight +
        layer2.loan_risk_score * w.loan_weight +
        layer2.permission_risk_score * w.permission_weight +
        layer3.temporal_risk_score * w.temporal_weight +
        layer4.network_risk_score * w.network_weight
    )

    reasons = []

    # 1. Identity Overrides
    if layer1.website_match_status == "MISMATCH":
        reasons.append("Website-domain mismatch: Claimed regulated entity name does not match official registered domain")
        weighted_score = max(weighted_score, 88.0)
    elif layer1.website_match_status == "UNVERIFIED_ALIAS":
        reasons.append("Unlisted domain alias: Operating on marketing domain not listed in primary RBI registry record")
    elif layer1.website_match_status == "UNREGISTERED":
        reasons.append("Unregistered lender: No public RBI NBFC or lending registration found")
    elif layer1.website_match_status == "REVOKED_LICENSE":
        reasons.append("Revoked regulatory standing: Entity license has been cancelled by regulatory authority")
        weighted_score = max(weighted_score, 90.0)

    # 2. Loan Overrides
    if layer2.advance_fee_detected:
        reasons.append("Advance fee detected: Demands upfront fee or security deposit before loan disbursement")
        weighted_score = max(weighted_score, 88.0)
    
    if layer2.permission_risk_score >= 70.0:
        reasons.append(f"Dangerous device permission requests (Risk score: {layer2.permission_risk_score}/100)")

    if layer2.apr_risk_level == "PREDATORY":
        reasons.append(f"Predatory interest rate ({layer2.disclosed_apr}% APR) exceeding fair practices guidelines")

    # 3. LSTM Temporal Overrides
    if layer3.pattern_type == "ABNORMAL_BURST":
        reasons.append(f"Abnormal temporal activity: Grievance and inquiry volume spiked {layer3.burst_multiplier}x above baseline")
        weighted_score = max(weighted_score, 80.0)
    elif layer3.pattern_type == "COMPLAINT_SPIKE":
        reasons.append("Elevated temporal complaint frequency in recent monitoring window")

    # 4. GNN Network Overrides
    if layer4.connected_flagged_domains > 0 or layer4.connected_suspicious_accounts > 0:
        reasons.append(
            f"Suspicious network graph relationships: Linked to {layer4.connected_flagged_domains} flagged domain(s) and {layer4.connected_suspicious_accounts} suspicious payment account(s)"
        )
        weighted_score = max(weighted_score, 85.0)

    final_score = round(min(max(weighted_score, 5.0), 99.0), 1)

    # Classify Risk Level & Decision
    if final_score <= LOW_RISK_THRESHOLD:
        risk_level = "LOW"
        decision = "ALLOW"
        if not reasons:
            reasons.append("Official registered entity with verified domain, transparent terms, and clean network graph")
    elif final_score <= MEDIUM_RISK_THRESHOLD:
        risk_level = "UNCERTAIN"
        decision = "HUMAN_REVIEW"
        if not reasons:
            reasons.append("Inconclusive evidence: Unverified domain alias or incomplete regulatory disclosure")
    elif final_score <= HIGH_RISK_THRESHOLD:
        risk_level = "HIGH"
        decision = "WARN"
    else:
        risk_level = "CRITICAL"
        decision = "BLOCK"

    # Confidence calculation based on evidence convergence
    layer_scores = [
        layer1.identity_consistency_score,
        layer2.loan_risk_score,
        layer2.permission_risk_score,
        layer3.temporal_risk_score,
        layer4.network_risk_score
    ]
    std_dev = (sum((s - (sum(layer_scores) / len(layer_scores))) ** 2 for s in layer_scores) / len(layer_scores)) ** 0.5
    confidence = round(max(0.70, min(0.98, 1.0 - (std_dev / 200.0))), 2)

    return RiskFusionResult(
        risk_score=final_score,
        risk_level=risk_level,
        decision=decision,
        confidence=confidence,
        reasons=reasons,
        weights_used={
            "identity_weight": w.identity_weight,
            "loan_weight": w.loan_weight,
            "permission_weight": w.permission_weight,
            "temporal_weight": w.temporal_weight,
            "network_weight": w.network_weight
        },
        identity=layer1,
        loan_risk=layer2,
        lstm=layer3,
        gnn=layer4,
        disclaimer=PROTOTYPE_DISCLAIMER
    )
