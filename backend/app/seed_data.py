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

    # 1. Seed Government & Regulatory Registry (including Govt Portals, Banks, Top NBFCs)
    # Schema: lender_id, legal_name, registration_number, status, official_domain, official_phone, registration_date, regulator
    govt_records = [
        # Official Government Portals & National Credit Initiatives
        (
            "gov_jansamarth",
            "JanSamarth — National Portal for Credit-Linked Government Schemes",
            "GOV-INIT-MIN-FIN",
            "ACTIVE",
            "jansamarth.in",
            "1800-11-5565",
            "2022-06-10",
            "Ministry of Finance (Government of India)"
        ),
        (
            "gov_mudra",
            "Pradhan Mantri MUDRA Yojana (PMMY)",
            "GOV-MUDRA-PMMY",
            "ACTIVE",
            "mudra.org.in",
            "1800-180-1111",
            "2015-04-08",
            "Department of Financial Services (DFS)"
        ),
        (
            "gov_psb59",
            "PSB Loans in 59 Minutes",
            "GOV-SIDBI-PSB59",
            "ACTIVE",
            "psbloansin59minutes.com",
            "079-41055999",
            "2018-11-02",
            "SIDBI / Ministry of Finance"
        ),
        (
            "gov_vidyalakshmi",
            "Vidya Lakshmi Education Loan Portal",
            "GOV-NSDL-VIDYA",
            "ACTIVE",
            "vidyalakshmi.co.in",
            "022-24997000",
            "2015-08-15",
            "Ministry of Education (Govt of India)"
        ),
        (
            "gov_standup",
            "Stand-Up India Portal",
            "GOV-SIDBI-STANDUP",
            "ACTIVE",
            "standupmitra.in",
            "1800-180-1111",
            "2016-04-05",
            "SIDBI / Government of India"
        ),

        # Scheduled Commercial Banks
        (
            "bank_sbi",
            "State Bank of India (SBI)",
            "BANK-SCHEDULED-SBI-001",
            "ACTIVE",
            "sbi.co.in",
            "1800-1234",
            "1955-07-01",
            "Reserve Bank of India (RBI)"
        ),
        (
            "bank_hdfc",
            "HDFC Bank Limited",
            "BANK-SCHEDULED-HDFC-002",
            "ACTIVE",
            "hdfcbank.com",
            "1800-202-6161",
            "1994-08-05",
            "Reserve Bank of India (RBI)"
        ),
        (
            "bank_icici",
            "ICICI Bank Limited",
            "BANK-SCHEDULED-ICICI-003",
            "ACTIVE",
            "icicibank.com",
            "1800-1080",
            "1994-01-05",
            "Reserve Bank of India (RBI)"
        ),
        (
            "bank_axis",
            "Axis Bank Limited",
            "BANK-SCHEDULED-AXIS-004",
            "ACTIVE",
            "axisbank.com",
            "1800-419-5959",
            "1993-12-03",
            "Reserve Bank of India (RBI)"
        ),
        (
            "bank_kotak",
            "Kotak Mahindra Bank Limited",
            "BANK-SCHEDULED-KOTAK-005",
            "ACTIVE",
            "kotak.com",
            "1860-266-2666",
            "2003-02-11",
            "Reserve Bank of India (RBI)"
        ),
        (
            "bank_pnb",
            "Punjab National Bank (PNB)",
            "BANK-SCHEDULED-PNB-006",
            "ACTIVE",
            "pnbindia.in",
            "1800-180-2222",
            "1894-05-19",
            "Reserve Bank of India (RBI)"
        ),
        (
            "bank_bob",
            "Bank of Baroda",
            "BANK-SCHEDULED-BOB-007",
            "ACTIVE",
            "bankofbaroda.in",
            "1800-5700",
            "1908-07-20",
            "Reserve Bank of India (RBI)"
        ),

        # Registered NBFCs & Digital Lenders
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
            "lender_muthoot",
            "Muthoot Finance Limited",
            "NBFC-MUTHOOT-0089",
            "ACTIVE",
            "muthootfinance.com",
            "1800-313-1212",
            "1997-03-14",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_shriram",
            "Shriram Finance Limited",
            "NBFC-SHRIRAM-0021",
            "ACTIVE",
            "shriramfinance.in",
            "1800-103-4959",
            "1979-05-09",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_lendingkart",
            "Lendingkart Finance Limited",
            "NBFC-LENDINGKART-014",
            "ACTIVE",
            "lendingkart.com",
            "1800-572-0202",
            "2015-06-18",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_kreditbee",
            "Krazybee Services Private Limited (KreditBee)",
            "NBFC-KRAZYBEE-099",
            "ACTIVE",
            "kreditbee.in",
            "080-44292200",
            "2017-05-12",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_navi",
            "Navi Finserv Limited",
            "NBFC-NAVI-00312",
            "ACTIVE",
            "navi.com",
            "080-45663333",
            "2019-12-01",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_moneyview",
            "Whizdm Innovations Pvt Ltd (Moneyview)",
            "NBFC-WHIZDM-041",
            "ACTIVE",
            "moneyview.in",
            "080-69390476",
            "2014-04-10",
            "Reserve Bank of India (RBI)"
        ),
        (
            "lender_paisabazaar",
            "Paisabazaar Marketing and Consulting Pvt Ltd",
            "AGG-PAISABAZAAR-01",
            "ACTIVE",
            "paisabazaar.com",
            "1800-208-8877",
            "2014-02-14",
            "Direct Lending Platform & Marketplace"
        ),
        (
            "lender_bankbazaar",
            "BankBazaar (A & A Dukaan Financial Services)",
            "AGG-BANKBAZAAR-02",
            "ACTIVE",
            "bankbazaar.com",
            "044-66511800",
            "2008-05-20",
            "Direct Lending Platform & Marketplace"
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
        )
    ]

    cursor.executemany("""
    INSERT INTO government_registry 
    (lender_id, legal_name, registration_number, status, official_domain, official_phone, registration_date, regulator)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, govt_records)

    # 2. Seed Graph Nodes
    nodes = [
        # Government / Public Portal Node
        ("node_gov_jansamarth", "GOVERNMENT_PORTAL", "jansamarth.in", "JanSamarth Government Portal", 0, 0, json.dumps({"verified": True, "gov": True})),
        
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

    # 4. Seed Temporal Activities
    now = datetime.utcnow()
    abc_sequence = [12, 14, 15, 13, 16, 14, 15, 17, 16]
    for i, val in enumerate(abc_sequence):
        t = (now - timedelta(days=(len(abc_sequence) - i) * 3)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO temporal_activities (entity_id, timestamp, activity_type, activity_value) VALUES (?, ?, ?, ?)",
                       ("abcfinance.com", t, "COMPLAINTS_AND_INQUIRIES", val))

    fc_sequence = [10, 12, 11, 14, 16, 18, 75, 180, 350]
    for i, val in enumerate(fc_sequence):
        t = (now - timedelta(days=(len(fc_sequence) - i) * 3)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO temporal_activities (entity_id, timestamp, activity_type, activity_value) VALUES (?, ?, ?, ?)",
                       ("fastcash-instantloans.net", t, "COMPLAINTS_AND_INQUIRIES", val))

    conn.commit()
    conn.close()
    print("Database seeded with comprehensive reference data including Government Portals, Scheduled Banks, and Verified NBFCs!")

if __name__ == "__main__":
    seed_database()
