import json
import sqlite3
from datetime import datetime, timedelta
from database import get_db_connection, init_db

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing reference tables
    cursor.execute("DELETE FROM government_registry;")
    cursor.execute("DELETE FROM graph_nodes;")
    cursor.execute("DELETE FROM graph_edges;")
    cursor.execute("DELETE FROM temporal_activities;")
    cursor.execute("DELETE FROM cases;")

    # 1. Seed Government Registry
    # Schema: lender_id, legal_name, registration_number, status, official_domain, official_phone, registration_date, regulator
    govt_records = [
        (
            "lender_abc_finance",
            "ABC Finance Ltd.",
            "NBFC-CORP-109482",
            "ACTIVE",
            "abcfinance.com",
            "+91-22-68940000",
            "2016-04-12",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_quickloan_nbfc",
            "QuickLoan Financial Services Ltd.",
            "NBFC-ND-SI-992144",
            "ACTIVE",
            "quickloanfinance.org",
            "+91-11-45892211",
            "2020-09-18",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_tata_capital",
            "Tata Capital Financial Services Limited",
            "NBFC-TATA-00129",
            "ACTIVE",
            "tatacapital.com",
            "+91-22-66069000",
            "2011-01-05",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_bajaj_finserv",
            "Bajaj Finance Limited",
            "NBFC-BAJAJ-00441",
            "ACTIVE",
            "bajajfinserv.in",
            "+91-20-71576403",
            "2007-03-25",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_habb_lending",
            "Habb Lending Microcredit Inc.",
            "NBFC-REVOKED-4410",
            "REVOKED",
            "habblending.in",
            "+91-80-33445566",
            "2018-06-11",
            "Reserve Bank of India (RBI)"
        )
    ]

    cursor.executemany("""
    INSERT INTO government_registry 
    (lender_id, legal_name, registration_number, status, official_domain, official_phone, registration_date, regulator)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, govt_records)

    # 2. Seed Graph Nodes
    # Entities: LENDER, DOMAIN, PHONE, APP, PAYMENT_ACCOUNT, UPI_ID, BANK_ACCOUNT
    nodes = [
        # ABC Finance (Legitimate Cluster)
        ("node_lender_abc", "LENDER", "ABC Finance Ltd.", "ABC Finance Ltd.", 0, 10, json.dumps({"verified": True})),
        ("node_domain_abc", "DOMAIN", "abcfinance.com", "abcfinance.com", 0, 8, json.dumps({"official": True})),
        ("node_phone_abc", "PHONE", "+91-22-68940000", "+91-22-68940000", 0, 5, json.dumps({"registered": True})),
        ("node_app_abc", "APP", "ABC Finance Mobile", "ABC Finance Mobile", 0, 12, json.dumps({"downloads": "1M+"})),
        ("node_acc_abc", "PAYMENT_ACCOUNT", "HDFC_CORP_99812", "HDFC Corp Settlement", 0, 5, json.dumps({"kyc": "verified"})),

        # QuickLoan (Uncertain Cluster)
        ("node_lender_ql", "LENDER", "QuickLoan Financial Services Ltd.", "QuickLoan Financial", 0, 45, json.dumps({"flagged": False})),
        ("node_domain_ql_official", "DOMAIN", "quickloanfinance.org", "quickloanfinance.org (Official)", 0, 20, json.dumps({"status": "active"})),
        ("node_domain_ql_active", "DOMAIN", "quickloan-app.in", "quickloan-app.in (Unregistered Alias)", 1, 55, json.dumps({"status": "unverified_alias"})),
        ("node_phone_ql", "PHONE", "+91-9820011223", "+91-9820011223", 0, 35, json.dumps({"carrier": "Airtel"})),
        ("node_upi_ql", "UPI_ID", "quickloan@icici", "quickloan@icici", 0, 40, json.dumps({"type": "merchant_upi"})),

        # FastCash Fraud Network Cluster
        ("node_domain_fc", "DOMAIN", "fastcash-instantloans.net", "fastcash-instantloans.net", 1, 95, json.dumps({"flagged": True, "reason": "phishing/advance-fee"})),
        ("node_domain_oldloan", "DOMAIN", "rupee-instant-loan.xyz", "rupee-instant-loan.xyz (Flagged)", 1, 98, json.dumps({"flagged": True, "status": "blocked_by_cert"})),
        ("node_domain_ezcash", "DOMAIN", "ezcash-fastloan.online", "ezcash-fastloan.online (Flagged)", 1, 92, json.dumps({"flagged": True})),
        ("node_phone_shared_fraud", "PHONE", "+91-9988776655", "+91-9988776655 (Syndicate Hotline)", 1, 90, json.dumps({"flagged": True, "spam_score": 94})),
        ("node_upi_fraud_1", "UPI_ID", "fastpay.collect@okhdfcbank", "fastpay.collect@okhdfcbank", 1, 96, json.dumps({"flagged": True, "fraud_reports": 28})),
        ("node_upi_fraud_2", "UPI_ID", "instantdisburse.mule@paytm", "instantdisburse.mule@paytm (Mule UPI)", 1, 94, json.dumps({"flagged": True, "kyc_fake": True})),
        ("node_acc_mule", "BANK_ACCOUNT", "YESB0000491-992817263", "Yes Bank Mule Account", 1, 95, json.dumps({"flagged": True, "frozen": True})),
        ("node_app_predatory", "APP", "Fast Cash Quick Loan APK", "Fast Cash APK (Sideloaded)", 1, 99, json.dumps({"flagged": True, "permissions": ["contacts", "sms", "location"]}))
    ]

    cursor.executemany("""
    INSERT INTO graph_nodes (id, entity_type, entity_value, label, is_suspicious, risk_score, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, nodes)

    # 3. Seed Graph Edges
    # relation_types: USES, OWNS, CONNECTED_TO, REGISTERED_AS, PAYS_TO, SHARES_PHONE, SHARES_DOMAIN, SHARES_ACCOUNT
    edges = [
        # ABC Finance Edges
        ("edge_1", "node_lender_abc", "node_domain_abc", "REGISTERED_AS", 0),
        ("edge_2", "node_lender_abc", "node_phone_abc", "USES", 0),
        ("edge_3", "node_lender_abc", "node_app_abc", "OWNS", 0),
        ("edge_4", "node_app_abc", "node_acc_abc", "PAYS_TO", 0),

        # QuickLoan Edges
        ("edge_5", "node_lender_ql", "node_domain_ql_official", "REGISTERED_AS", 0),
        ("edge_6", "node_domain_ql_active", "node_lender_ql", "CONNECTED_TO", 1),
        ("edge_7", "node_domain_ql_active", "node_phone_ql", "USES", 0),
        ("edge_8", "node_domain_ql_active", "node_upi_ql", "PAYS_TO", 0),

        # FastCash Fraud Syndicate Mesh
        ("edge_9",  "node_domain_fc", "node_phone_shared_fraud", "SHARES_PHONE", 1),
        ("edge_10", "node_domain_oldloan", "node_phone_shared_fraud", "SHARES_PHONE", 1),
        ("edge_11", "node_domain_fc", "node_upi_fraud_1", "PAYS_TO", 1),
        ("edge_12", "node_domain_fc", "node_app_predatory", "CONNECTED_TO", 1),
        ("edge_13", "node_domain_oldloan", "node_upi_fraud_1", "CONNECTED_TO", 1),
        ("edge_14", "node_domain_ezcash", "node_phone_shared_fraud", "SHARES_PHONE", 1),
        ("edge_15", "node_domain_ezcash", "node_upi_fraud_2", "PAYS_TO", 1),
        ("edge_16", "node_upi_fraud_1", "node_acc_mule", "CONNECTED_TO", 1),
        ("edge_17", "node_upi_fraud_2", "node_acc_mule", "SHARES_ACCOUNT", 1),
        ("edge_18", "node_app_predatory", "node_upi_fraud_1", "PAYS_TO", 1)
    ]

    cursor.executemany("""
    INSERT INTO graph_edges (id, source_id, target_id, relation_type, is_suspicious)
    VALUES (?, ?, ?, ?, ?);
    """, edges)

    # 4. Seed Temporal Activities (LSTM sequences)
    # Sequence types: Normal organic, Moderate fluctuation, Sudden burst anomaly
    now = datetime.utcnow()

    # Normal sequence for ABC Finance
    abc_sequence = [12, 14, 15, 13, 16, 14, 15, 17, 16]
    for i, val in enumerate(abc_sequence):
        t = (now - timedelta(days=(len(abc_sequence) - i) * 3)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO temporal_activities (entity_id, timestamp, activity_type, activity_value) VALUES (?, ?, ?, ?)",
                       ("abcfinance.com", t, "COMPLAINTS_AND_INQUIRIES", val))

    # Moderate sequence for QuickLoan
    ql_sequence = [20, 24, 22, 28, 35, 42, 48, 55, 58]
    for i, val in enumerate(ql_sequence):
        t = (now - timedelta(days=(len(ql_sequence) - i) * 3)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO temporal_activities (entity_id, timestamp, activity_type, activity_value) VALUES (?, ?, ?, ?)",
                       ("quickloan-app.in", t, "COMPLAINTS_AND_INQUIRIES", val))

    # Burst sequence for FastCash: [10, 12, 11, 14, 16, 18, 75, 180, 350]
    fc_sequence = [10, 12, 11, 14, 16, 18, 75, 180, 350]
    for i, val in enumerate(fc_sequence):
        t = (now - timedelta(days=(len(fc_sequence) - i) * 3)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO temporal_activities (entity_id, timestamp, activity_type, activity_value) VALUES (?, ?, ?, ?)",
                       ("fastcash-instantloans.net", t, "COMPLAINTS_AND_INQUIRIES", val))

    # 5. Pre-seed Benchmark Cases for the Analyst Dashboard
    cases = [
        (
            "case_fc_001",
            "lender_fastcash",
            "ABC Finance (Impersonated)",
            "fastcash-instantloans.net",
            "https://fastcash-instantloans.net/apply",
            91.0,
            "HIGH",
            "BLOCK",
            0.94,
            json.dumps([
                "Website-Domain mismatch (Impersonating ABC Finance Ltd.)",
                "Advance fee of ₹1,500 demanded before loan disbursement",
                "Connected to 3 previously flagged domains via shared phone hotline",
                "Mule UPI payment receiver fastpay.collect@okhdfcbank detected",
                "Abnormal burst in temporal activity / consumer grievance volume (+1840%)"
            ]),
            json.dumps({
                "identity": {"consistency_score": 90, "claimed": "ABC Finance Ltd.", "official_domain": "abcfinance.com", "actual_domain": "fastcash-instantloans.net", "match": "FAILED"},
                "loan_risk": {"score": 85, "advance_fee": True, "fee_amount": 1500, "kfs": False, "urgency": True},
                "permission_risk": {"score": 95, "permissions": ["Contacts (HIGH)", "SMS (HIGH)", "Media (HIGH)", "Location (MEDIUM)"]},
                "lstm": {"score": 88, "pattern": "ABNORMAL_BURST", "burst_multiplier": 19.4},
                "gnn": {"score": 92, "flagged_domains": 3, "suspicious_accounts": 2, "reported_phones": 1}
            }),
            "PENDING",
            None,
            "",
            "",
            (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "case_ql_002",
            "lender_quickloan_nbfc",
            "QuickLoan Financial",
            "quickloan-app.in",
            "https://quickloan-app.in/loan-offer",
            56.0,
            "UNCERTAIN",
            "HUMAN_REVIEW",
            0.82,
            json.dumps([
                "Valid RBI registration found under legal entity, but unofficial domain alias used",
                "Key Fact Statement (KFS) format incomplete",
                "Contacts permission requested for references verification",
                "Elevated inquiry trend over past 30 days"
            ]),
            json.dumps({
                "identity": {"consistency_score": 45, "claimed": "QuickLoan Financial Services Ltd.", "official_domain": "quickloanfinance.org", "actual_domain": "quickloan-app.in", "match": "INCONCLUSIVE"},
                "loan_risk": {"score": 52, "advance_fee": False, "kfs": False, "apr": 38.5},
                "permission_risk": {"score": 60, "permissions": ["Contacts (HIGH)", "Location (MEDIUM)"]},
                "lstm": {"score": 58, "pattern": "MODERATE_ELEVATION", "burst_multiplier": 2.4},
                "gnn": {"score": 45, "flagged_domains": 0, "suspicious_accounts": 0, "reported_phones": 0}
            }),
            "PENDING",
            None,
            "",
            "",
            (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "case_abc_003",
            "lender_abc_finance",
            "ABC Finance Ltd.",
            "abcfinance.com",
            "https://abcfinance.com/personal-loan",
            18.0,
            "LOW",
            "ALLOW",
            0.96,
            json.dumps([
                "Direct match with official RBI Registered NBFC registry record",
                "Domain abcfinance.com fully verified with SSL & MCA registration",
                "Comprehensive Key Fact Statement (KFS) disclosed with transparent APR (14.5%)",
                "No advance fees or abusive permissions requested",
                "Network graph isolated from known fraudulent syndicates"
            ]),
            json.dumps({
                "identity": {"consistency_score": 5, "claimed": "ABC Finance Ltd.", "official_domain": "abcfinance.com", "actual_domain": "abcfinance.com", "match": "VERIFIED"},
                "loan_risk": {"score": 12, "advance_fee": False, "kfs": True, "apr": 14.5},
                "permission_risk": {"score": 10, "permissions": []},
                "lstm": {"score": 15, "pattern": "NORMAL_ORGANIC", "burst_multiplier": 1.05},
                "gnn": {"score": 8, "flagged_domains": 0, "suspicious_accounts": 0, "reported_phones": 0}
            }),
            "REVIEWED",
            "APPROVE",
            "Official licensed lender, fully compliant.",
            "analyst_1",
            (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
        )
    ]

    cursor.executemany("""
    INSERT INTO cases 
    (id, lender_id, claimed_name, domain, url, risk_score, risk_level, decision, confidence, reasons_json, evidence_json, status, analyst_action, analyst_notes, analyst_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, cases)

    conn.commit()
    conn.close()
    print("Database seeded with comprehensive reference data for Legitimate, Uncertain, and Fraudulent scenarios!")

if __name__ == "__main__":
    seed_database()
