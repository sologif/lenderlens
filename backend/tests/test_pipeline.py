import unittest
import os
import sys

# Add backend/app to path
BACKEND_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
if BACKEND_APP_DIR not in sys.path:
    sys.path.insert(0, BACKEND_APP_DIR)

from services.layer1_identity import verify_identity
from services.layer2_loan_risk import analyze_loan_and_permissions
from services.layer3_lstm import analyze_temporal_risk
from services.layer4_gnn import analyze_network_risk
from services.risk_fusion import fuse_risk_scores
from database import init_db
from seed_data import seed_database

class TestLenderLensPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        seed_database()

    def test_legitimate_scenario_abc_finance(self):
        """Tests that ABC Finance Ltd. is correctly classified as LOW risk (ALLOW)."""
        l1 = verify_identity(claimed_name="ABC Finance Ltd.", domain="abcfinance.com")
        self.assertEqual(l1.website_match_status, "MATCHED")
        self.assertLessEqual(l1.identity_consistency_score, 10.0)

        l2 = analyze_loan_and_permissions(has_kfs=True, apr=14.5, advance_fee_requested=False)
        self.assertFalse(l2.advance_fee_detected)
        self.assertLessEqual(l2.loan_risk_score, 20.0)

        l3 = analyze_temporal_risk(domain="abcfinance.com")
        self.assertEqual(l3.pattern_type, "NORMAL_ORGANIC")

        l4 = analyze_network_risk(domain="abcfinance.com")
        self.assertEqual(l4.connected_flagged_domains, 0)

        fusion = fuse_risk_scores(l1, l2, l3, l4)
        self.assertEqual(fusion.risk_level, "LOW")
        self.assertEqual(fusion.decision, "ALLOW")
        self.assertLessEqual(fusion.risk_score, 30.0)

    def test_uncertain_scenario_quickloan(self):
        """Tests that QuickLoan unlisted alias is classified as UNCERTAIN (HUMAN_REVIEW)."""
        l1 = verify_identity(claimed_name="QuickLoan Financial Services Ltd.", domain="quickloan-app.in")
        self.assertEqual(l1.website_match_status, "UNVERIFIED_ALIAS")

        l2 = analyze_loan_and_permissions(has_kfs=False, apr=38.5, permissions_requested=["contacts", "location"])
        self.assertGreater(l2.permission_risk_score, 30.0)

        l3 = analyze_temporal_risk(domain="quickloan-app.in")
        l4 = analyze_network_risk(domain="quickloan-app.in")

        fusion = fuse_risk_scores(l1, l2, l3, l4)
        self.assertEqual(fusion.risk_level, "UNCERTAIN")
        self.assertEqual(fusion.decision, "HUMAN_REVIEW")
        self.assertGreaterEqual(fusion.risk_score, 31.0)
        self.assertLessEqual(fusion.risk_score, 60.0)

    def test_fraudulent_scenario_fastcash_impersonation(self):
        """Tests that FastCash impersonating ABC Finance with advance fee is classified as CRITICAL (BLOCK)."""
        l1 = verify_identity(claimed_name="ABC Finance Ltd.", domain="fastcash-instantloans.net")
        self.assertEqual(l1.website_match_status, "MISMATCH")
        self.assertGreaterEqual(l1.identity_consistency_score, 85.0)

        l2 = analyze_loan_and_permissions(
            page_text="Advance fee required! Guaranteed approval in 2 minutes!",
            permissions_requested=["contacts", "sms", "call logs", "media", "photos"],
            advance_fee_requested=True
        )
        self.assertTrue(l2.advance_fee_detected)
        self.assertGreaterEqual(l2.permission_risk_score, 90.0)

        l3 = analyze_temporal_risk(domain="fastcash-instantloans.net")
        self.assertEqual(l3.pattern_type, "ABNORMAL_BURST")

        l4 = analyze_network_risk(domain="fastcash-instantloans.net")
        self.assertGreaterEqual(l4.connected_flagged_domains, 1)

        fusion = fuse_risk_scores(l1, l2, l3, l4)
        self.assertIn(fusion.risk_level, ["HIGH", "CRITICAL"])
        self.assertEqual(fusion.decision, "BLOCK")
        self.assertGreaterEqual(fusion.risk_score, 85.0)

if __name__ == "__main__":
    unittest.main()
