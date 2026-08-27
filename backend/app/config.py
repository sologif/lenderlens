# Configuration for LenderLens Risk Fusion Engine & Services

from pydantic import BaseModel
from typing import Dict

class RiskWeights(BaseModel):
    identity_weight: float = 0.25      # Layer 1: Identity & Govt mismatch
    loan_weight: float = 0.20          # Layer 2a: Loan indicators (KFS, APR, advance fee)
    permission_weight: float = 0.15    # Layer 2b: Dangerous permissions
    temporal_weight: float = 0.20      # Layer 3: LSTM Temporal anomaly score
    network_weight: float = 0.20       # Layer 4: GNN Graph risk score

DEFAULT_WEIGHTS = RiskWeights()

# Risk Thresholds
LOW_RISK_THRESHOLD = 30       # <= 30 -> LOW (Allow)
MEDIUM_RISK_THRESHOLD = 60    # 31 - 60 -> UNCERTAIN (Human Review)
HIGH_RISK_THRESHOLD = 75      # 61 - 75 -> HIGH (Warn)
CRITICAL_RISK_THRESHOLD = 100 # > 75 -> CRITICAL (Block)

# Prototype Disclaimer
PROTOTYPE_DISCLAIMER = (
    "Prototype Notice: Government/regulatory records, fraud histories, LSTM sequences, "
    "and GNN relationships shown in this demonstration use reference/simulated prototype data. "
    "Production deployment requires authorized regulatory data sources, validated datasets, "
    "security review, and production model calibration."
)
