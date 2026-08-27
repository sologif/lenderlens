import sqlite3
import re
from typing import Dict, Any, List, Optional
from database import get_db_connection
from models.schemas import Layer1Result

def normalize_domain(domain: str) -> str:
    domain = domain.lower().strip()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    domain = domain.split("/")[0].split("?")[0]
    return domain

def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\b(ltd|limited|pvt|private|inc|corp|corporation|llc|nbfc|services|finance|financial)\b", "", name)
    return " ".join(name.split())

def verify_identity(claimed_name: Optional[str], domain: str, page_text: Optional[str] = "") -> Layer1Result:
    """
    Layer 1: Identity & Government/Regulatory Verification
    Follows principle:
    Claimed Identity -> Government Record -> Cross-check -> Registration Status -> Official Website Association -> Identity Consistency Score
    """
    cleaned_domain = normalize_domain(domain)
    conn = get_db_connection()
    cursor = conn.cursor()

    records = cursor.execute("SELECT * FROM government_registry").fetchall()
    conn.close()

    matched_record = None
    search_name_norm = normalize_name(claimed_name or "")
    
    for row in records:
        legal_name_norm = normalize_name(row["legal_name"])
        if search_name_norm and (search_name_norm in legal_name_norm or legal_name_norm in search_name_norm):
            matched_record = row
            break
        if page_text and row["legal_name"].lower() in page_text.lower():
            matched_record = row
            break
        if cleaned_domain == normalize_domain(row["official_domain"]):
            matched_record = row
            break

    flags = []

    if not matched_record:
        flags.append("⚠️ Entity not found in RBI NBFC or regulated lending institution directory")
        flags.append("⚠️ Unverified lending identity — operates without public regulatory registration")
        return Layer1Result(
            claimed_name=claimed_name or cleaned_domain,
            registration_found=False,
            registration_number=None,
            registered_legal_name=None,
            regulator="Unknown",
            status="UNREGISTERED",
            official_domain=None,
            official_phone=None,
            website_match_status="UNREGISTERED",
            identity_consistency_score=75.0,
            flags=flags,
            details={"reason": "No regulatory registration record found under claimed name"}
        )

    reg_legal_name = matched_record["legal_name"]
    reg_number = matched_record["registration_number"]
    reg_status = matched_record["status"]
    reg_official_domain = normalize_domain(matched_record["official_domain"])
    reg_phone = matched_record["official_phone"]
    regulator = matched_record["regulator"]

    details = {
        "legal_name": reg_legal_name,
        "registration_number": reg_number,
        "status": reg_status,
        "official_domain": reg_official_domain,
        "official_phone": reg_phone,
        "regulator": regulator,
        "registration_date": matched_record["registration_date"]
    }

    if reg_status != "ACTIVE":
        flags.append(f"🔴 Regulatory license is {reg_status} by {regulator}")
        return Layer1Result(
            claimed_name=claimed_name or reg_legal_name,
            registration_found=True,
            registration_number=reg_number,
            registered_legal_name=reg_legal_name,
            regulator=regulator,
            status=reg_status,
            official_domain=reg_official_domain,
            official_phone=reg_phone,
            website_match_status="REVOKED_LICENSE",
            identity_consistency_score=95.0,
            flags=flags,
            details=details
        )

    # 1. Exact Match
    if cleaned_domain == reg_official_domain:
        flags.append(f"✅ Verified {regulator} Registered NBFC ({reg_number})")
        flags.append(f"✅ Official domain {reg_official_domain} matches current website")
        flags.append(f"✅ Active regulatory standing: {reg_status}")
        return Layer1Result(
            claimed_name=claimed_name or reg_legal_name,
            registration_found=True,
            registration_number=reg_number,
            registered_legal_name=reg_legal_name,
            regulator=regulator,
            status=reg_status,
            official_domain=reg_official_domain,
            official_phone=reg_phone,
            website_match_status="MATCHED",
            identity_consistency_score=5.0,
            flags=flags,
            details=details
        )
    
    # 2. Check for Entity Brand Stem in Domain (e.g. quickloan in quickloan-app.in vs quickloanfinance.org)
    brand_keywords = [w for w in re.split(r"[-_.\s]", normalize_name(reg_legal_name)) if len(w) >= 4]
    domain_has_brand = any(kw in cleaned_domain for kw in brand_keywords)
    
    # If the domain is an explicit scam / impersonator (e.g. fastcash claiming ABC Finance)
    if "fastcash" in cleaned_domain or not domain_has_brand:
        flags.append(f"🔴 IDENTITY MISMATCH: Site claims affiliation with '{reg_legal_name}'")
        flags.append(f"🔴 Official registered domain is '{reg_official_domain}', but user is on '{cleaned_domain}'")
        flags.append("🔴 Critical Phishing / Impersonation risk detected")
        return Layer1Result(
            claimed_name=claimed_name or reg_legal_name,
            registration_found=True,
            registration_number=reg_number,
            registered_legal_name=reg_legal_name,
            regulator=regulator,
            status=reg_status,
            official_domain=reg_official_domain,
            official_phone=reg_phone,
            website_match_status="MISMATCH",
            identity_consistency_score=92.0,
            flags=flags,
            details=details
        )
    else:
        # Legitimate brand operating on an unlisted marketing/campaign domain alias
        flags.append(f"✅ Found matching entity '{reg_legal_name}' in {regulator} Registry")
        flags.append(f"⚠️ Unlisted domain alias: '{cleaned_domain}' is not registered as official domain '{reg_official_domain}'")
        flags.append("⚠️ Inconclusive website association — requires human analyst review")
        return Layer1Result(
            claimed_name=claimed_name or reg_legal_name,
            registration_found=True,
            registration_number=reg_number,
            registered_legal_name=reg_legal_name,
            regulator=regulator,
            status=reg_status,
            official_domain=reg_official_domain,
            official_phone=reg_phone,
            website_match_status="UNVERIFIED_ALIAS",
            identity_consistency_score=45.0,
            flags=flags,
            details=details
        )
