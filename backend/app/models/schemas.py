from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PageAnalyzeRequest(BaseModel):
    url: str
    domain: str
    claimed_lender: Optional[str] = None
    page_title: Optional[str] = None
    page_text: Optional[str] = None
    permissions_requested: Optional[List[str]] = Field(default_factory=list)
    has_kfs: Optional[bool] = None
    apr: Optional[float] = None
    advance_fee_requested: Optional[bool] = None
    payment_info: Optional[Dict[str, Any]] = None

class PaymentAnalyzeRequest(BaseModel):
    url: str
    domain: str
    lender_id: Optional[str] = None
    claimed_lender: Optional[str] = None
    upi_id: Optional[str] = None
    bank_account: Optional[str] = None
    payment_gateway: Optional[str] = None
    amount_requested: Optional[float] = None
    payment_type: Optional[str] = "advance_fee" # advance_fee, processing_fee, disbursement

class Layer1Result(BaseModel):
    claimed_name: str
    registration_found: bool
    registration_number: Optional[str] = None
    registered_legal_name: Optional[str] = None
    regulator: Optional[str] = None
    status: Optional[str] = None
    official_domain: Optional[str] = None
    official_phone: Optional[str] = None
    website_match_status: str # MATCHED, MISMATCH, NOT_FOUND, UNREGISTERED
    identity_consistency_score: float # 0 - 100 (higher = riskier / inconsistent)
    flags: List[str]
    details: Dict[str, Any]

class Layer2Result(BaseModel):
    kfs_available: bool
    disclosed_apr: Optional[float] = None
    apr_risk_level: str # NORMAL, HIGH, PREDATORY, UNDISCLOSED
    advance_fee_detected: bool
    urgency_language_detected: bool
    repayment_period_days: Optional[int] = None
    permission_risk_score: float # 0 - 100
    detected_permissions: List[Dict[str, str]] # e.g. [{"name": "Contacts", "risk": "HIGH"}]
    loan_risk_score: float # 0 - 100
    flags: List[str]
    details: Dict[str, Any]

class Layer3Result(BaseModel):
    temporal_risk_score: float # 0 - 100
    pattern_type: str # NORMAL_ORGANIC, ABNORMAL_BURST, COMPLAINT_SPIKE, INACTIVE_DORMANT
    sequence_data: List[Dict[str, Any]] # [{"timestamp": "...", "activity_value": 10, ...}]
    anomaly_detected: bool
    burst_multiplier: float
    flags: List[str]
    details: Dict[str, Any]

class Layer4Result(BaseModel):
    network_risk_score: float # 0 - 100
    connected_flagged_domains: int
    connected_suspicious_accounts: int
    connected_reported_phones: int
    centrality_score: float
    subgraph_nodes: List[Dict[str, Any]]
    subgraph_edges: List[Dict[str, Any]]
    flags: List[str]
    details: Dict[str, Any]

class RiskFusionResult(BaseModel):
    risk_score: float # 0 - 100
    risk_level: str # LOW, UNCERTAIN, HIGH, CRITICAL
    decision: str # ALLOW, HUMAN_REVIEW, WARN, BLOCK
    confidence: float # 0.0 - 1.0
    reasons: List[str]
    weights_used: Dict[str, float]
    identity: Layer1Result
    loan_risk: Layer2Result
    lstm: Layer3Result
    gnn: Layer4Result
    disclaimer: str

class CaseReviewRequest(BaseModel):
    action: str # APPROVE, WARN, BLOCK, ESCALATE
    analyst_notes: Optional[str] = ""
    analyst_id: Optional[str] = "analyst_1"

class UserReportRequest(BaseModel):
    url: str
    domain: str
    lender_name: Optional[str] = ""
    reason: Optional[str] = ""
    details: Optional[str] = ""
