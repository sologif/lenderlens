# LenderLens Deliverables

## Core product

- Borrower-facing Chrome extension for real-time loan-site checks.
- Public product website that explains the problem, solution, architecture and value.
- Interactive website demo that reproduces the extension trust-card experience before installation.
- Analyst dashboard for case review and deeper evidence inspection.
- FastAPI backend connecting analysis, cases, registry and demo endpoints.

## Fraud-detection story

### Layer 1 — Identity & regulatory
Verify the claimed lender against the configured regulatory/reference registry and compare the current domain with the official domain.

### Layer 2 — Loan & permission risk
Inspect key loan disclosures, APR information, advance-fee signals, urgency language and invasive device permissions.

### Layer 3 — Temporal risk
Use activity sequences to identify abnormal complaint/inquiry bursts and velocity changes.

### Layer 4 — Network risk
Use graph relationships to identify clusters involving suspicious domains, phone numbers and payment endpoints.

### Risk fusion
Combine the evidence layers into an explainable score with three primary borrower outcomes: **ALLOW**, **REVIEW/WARN**, and **BLOCK**.

## Demo scenarios

- **ABC Finance:** verified / low risk / allow.
- **QuickLoan:** partially verified / uncertain / human review.
- **FastCash Instant Loans:** impersonation + advance fee + invasive permissions + suspicious network / high risk / block.

## Professional presentation requirements

- Consistent LenderLens branding across website, extension and analyst dashboard.
- Clear fintech/security visual language rather than a generic AI dashboard.
- Strong extension download/install CTA on the website.
- Live browser-style demonstration of a loan page beside the extension result.
- Clear explanation of why a result was produced; avoid presenting an unexplained score.
- Human-in-the-loop workflow for ambiguous cases.
- Explicit prototype/data disclaimer so simulated evidence is not presented as live regulatory data.
