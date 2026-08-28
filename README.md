# 🛡️ LenderLens — AI-Powered Loan Fraud Detection & Early-Warning System

LenderLens is a dual-interface AI loan fraud defense platform designed to protect retail borrowers from predatory lending apps, syndicate phishing portals, and advance fee scams in real-time.

```
┌─────────────────────────────────────────────────────────────┐
│                      LENDERLENS FLOW                        │
│                                                             │
│   Borrower visits loan site ──► Chrome Extension activates  │
│                                           │                 │
│         ┌─────────────────────────────────┴────────────┐    │
│         ▼                                              ▼    │
│  Layer 1: Identity & Govt Regulatory         Layer 2: Loan  │
│  (RBI Registry Cross-Check)               (KFS, APR, Perms) │
│         │                                              │    │
│         ▼                                              ▼    │
│  Layer 3: LSTM Temporal Risk               Layer 4: GNN Graph│
│  (Sequence Anomaly / Bursts)              (Syndicate Mesh)  │
│         └─────────────────┬────────────────────────────┘    │
│                           ▼                                 │
│                  RISK FUSION ENGINE                         │
│                           ▼                                 │
│              ┌────────────┴────────────┐                    │
│              ▼                         ▼                    │
│      Trust Card Injected      Analyst Dashboard Case        │
│    (Allow / Warn / Block)       (Human-in-the-Loop)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Live Demo (Zero Setup)

The prototype is fully deployed and running in the cloud. You do not need to install anything locally to evaluate the system.

**👉 Access the live system here:** [https://lenderlens-9rky.onrender.com](https://lenderlens-9rky.onrender.com)

From the live link, you can:
1. Try the interactive **Judge Simulator**.
2. View the **Analyst Console** (Human-in-the-loop dashboard).
3. Download the packaged **Chrome Extension** directly from the UI to test the live ML pipeline against the demo lender sites.

---

## 💻 Local Development (Optional)

If you prefer to run the API and dashboard locally, use the following commands:

```bash
# 1. Clone the repository and navigate to the directory
git clone https://github.com/sologif/lenderlens.git
cd lenderlens

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed the local SQLite database with RBI registry records
python backend/app/seed_data.py

# 4. Start the backend API and Dashboard
python -m uvicorn main:app --app-dir backend/app --host 0.0.0.0 --port 8000
```
The local server will start at **`http://localhost:8000`**.

---

### 🔌 Testing the Chrome Extension

1. Download the extension ZIP from the live site (or use the `extension/` folder if testing locally).
2. Open Google Chrome and navigate to `chrome://extensions/`.
3. Toggle on **Developer mode** in the top right corner.
4. Click **Load unpacked** and select the unzipped extension folder.
5. Visit one of the demo loan sites below to see the ML models and Trust Card in action!

---

## 🎯 Demo Scenarios

LenderLens comes with 3 pre-built interactive demo loan websites:

### 🟢 1. Legitimate Lender — ABC Finance
- **URL**: `https://lenderlens-9rky.onrender.com/demo/legitimate/index.html`
- **Result**: `✓ LOW RISK (18/100) — ALLOW`
- **Signals**: Verified RBI NBFC Registry record (`NBFC-CORP-109482`), official domain match (`abcfinance.com`), transparent Key Fact Statement (14.5% APR), ₹0 advance fee, clean isolated network graph.

### 🟡 2. Uncertain / Needs Review — QuickLoan
- **URL**: `https://lenderlens-9rky.onrender.com/demo/uncertain/index.html`
- **Result**: `⚠️ NEEDS REVIEW (56/100) — HUMAN REVIEW`
- **Signals**: Entity exists in RBI registry, but current domain (`quickloan-app.in`) is an unlisted marketing alias; partial KFS disclosure; contacts permission requested. Flagged for analyst investigation.

### 🔴 3. Fraudulent Syndicate — FastCash Instant Loans
- **URL**: `https://lenderlens-9rky.onrender.com/demo/fraudulent/index.html`
- **Result**: `🔴 HIGH RISK (91/100) — BLOCK`
- **Signals**:
  - **Identity Mismatch**: Claims affiliation with licensed "ABC Finance Ltd.", but operates on rogue domain `fastcash-instantloans.net`.
  - **Dangerous Permissions**: Demands Contacts, SMS, Call Logs, and Photos access.
  - **GNN Graph**: Connected to 3 flagged phishing domains & 2 mule UPI accounts via shared hotline `+91-9988776655`.
  - **LSTM Temporal Anomaly**: `[10, 12, 11, 14, 16, 18, 75, 180, 350]` (+1840% grievance volume burst).
  - **Advance Fee Payment**: Clicking to `payment.html` reveals an upfront ₹1,500 security deposit demand to mule UPI `fastpay.collect@okhdfcbank`.

---

## 🔬 Core Architecture

| Layer | Component | Implementation |
|---|---|---|
| **Layer 1** | Identity & Regulatory Cross-Check | Cross-checks claimed identity against RBI NBFC database and verifies official registered domains to prevent impersonation. |
| **Layer 2** | Loan & Permission Risk Engine | Inspects Key Fact Statements (KFS), APR disclosure, predatory urgency language, and scores invasive device permissions (Contacts, SMS, Media, Accessibility). |
| **Layer 3** | LSTM Temporal Risk | Sequence anomaly model evaluating 90-day grievance & inquiry sequences to detect abnormal velocity bursts. |
| **Layer 4** | GNN Network Risk | Graph Neural Network evaluating neighborhood connectivity to flagged domains, shared phone hotlines, and mule payment accounts. |
| **Risk Fusion** | Configurable Risk Engine | Combines parallel evidence layers using weighted fusion with critical override heuristics. |
| **Interface 1** | Trust Card (Chrome Extension) | Injected Shadow DOM floating security card + popup providing instant risk scores and evidence reasons. |
| **Interface 2** | Analyst Dashboard | Notion-inspired investigation console with interactive D3/Canvas GNN graph, LSTM sequence plots, and reviewer workflows (`APPROVE`, `WARN`, `BLOCK`, `ESCALATE`). |

---

## ⚠️ Prototype Notice
> **Disclaimer**: Government/regulatory records, fraud histories, LSTM sequences, and GNN relationships shown in this demonstration use simulated/reference prototype data. Production deployment requires authorized regulatory data sources, validated datasets, security review, and model validation.

---

## ☁️ Deploy to Render in 1 Click

To publish this unified prototype on **Render** as a web service:

1. Create a new **Web Service** on Render and link your GitHub repository.
2. Configure these build and startup settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python backend/download_and_parse_rbi.py`
   - **Start Command**: `python -m uvicorn main:app --app-dir backend/app --host 0.0.0.0 --port $PORT`
3. Click **Deploy Web Service**. LenderLens will be live on your custom Render subdomain!

