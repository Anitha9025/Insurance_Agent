from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate
from app.core.logging import logger

async def create_policy(db: AsyncSession, payload: PolicyCreate) -> Policy:
    """Creates a new policy record."""
    policy = Policy(
        policy_number=payload.policy_number,
        category=payload.category,
        start_date=payload.start_date,
        end_date=payload.end_date,
        premium_status=payload.premium_status,
        coverage_limit=payload.coverage_limit,
        deductible=payload.deductible,
        active_claims_count=payload.active_claims_count,
        customer_id=payload.customer_id
    )
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    logger.info(f"Created policy {policy.policy_number} for customer {policy.customer_id}")
    return policy

async def get_policy_by_number(db: AsyncSession, policy_number: str) -> Optional[Policy]:
    """Fetches policy by policy number."""
    stmt = select(Policy).where(Policy.policy_number == policy_number)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_policies(db: AsyncSession, customer_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Policy]:
    """Lists policies with optional customer filter."""
    stmt = select(Policy)
    if customer_id:
        stmt = stmt.where(Policy.customer_id == customer_id)
    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def list_policies_by_customer(db: AsyncSession, customer_id: str) -> List[Policy]:
    """Lists policies belonging to a specific customer."""
    return await list_policies(db, customer_id=customer_id)


def _parse_date_str(d_str: str) -> Optional[str]:
    """Converts '15 Feb 2026' or '15/02/2026' to 'YYYY-MM-DD'."""
    if not d_str:
        return None
    import re
    s = d_str.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    months = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m:
        day = int(m.group(1))
        mon_str = m.group(2).lower()[:3]
        year = int(m.group(3))
        if mon_str in months:
            return f"{year:04d}-{months[mon_str]:02d}-{day:02d}"
    m = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None


def _extract_policy_details_from_text(full_text: str) -> dict:
    import re
    extracted = {}
    if not full_text:
        return extracted

    # Category
    if re.search(r"\b(health|medical|hospitalization)\b", full_text, re.IGNORECASE):
        extracted["category"] = "Health"
    elif re.search(r"\b(home|property|building|house)\b", full_text, re.IGNORECASE):
        extracted["category"] = "Home"
    elif re.search(r"\b(travel|trip|flight)\b", full_text, re.IGNORECASE):
        extracted["category"] = "Travel"
    elif re.search(r"\b(vehicle|car|auto|motor)\b", full_text, re.IGNORECASE):
        extracted["category"] = "Vehicle"

    # Coverage Limit / Insured Declared Value (IDV) / Sum Insured
    idv_match = re.search(r"(?:Insured Declared Value \(IDV\)|Insured Declared Value|IDV)\s*[:|-]?\s*[■₹\$]?\s*([0-9,]+(?:\.[0-9]{2})?)", full_text, re.IGNORECASE)
    if idv_match:
        val_str = idv_match.group(1).replace(",", "")
        try:
            val_float = float(val_str)
            extracted["coverage_limit"] = val_float
            extracted["insured_declared_value"] = val_float
        except ValueError:
            pass

    if "coverage_limit" not in extracted:
        cov_match = re.search(r"(?:Sum Insured|Coverage Limit|Maximum Limit|Policy Limit)\s*[:|-]?\s*[■₹\$]?\s*([0-9,]+(?:\.[0-9]{2})?)", full_text, re.IGNORECASE)
        if cov_match:
            val_str = cov_match.group(1).replace(",", "")
            try:
                extracted["coverage_limit"] = float(val_str)
            except ValueError:
                pass

    # Deductible
    ded_match = re.search(r"(?:Own-Damage Deductible|Deductible|Policy Deductible)\s*[:|-]?\s*[■₹\$]?\s*([0-9,]+(?:\.[0-9]{2})?)", full_text, re.IGNORECASE)
    if ded_match:
        val_str = ded_match.group(1).replace(",", "")
        try:
            extracted["deductible"] = float(val_str)
        except ValueError:
            pass

    # Third-Party Liability Limit
    tp_match = re.search(r"Third-Party Liability Limit\s*[:|-]?\s*[■₹\$]?\s*([0-9,]+(?:\.[0-9]{2})?)", full_text, re.IGNORECASE)
    if tp_match:
        val_str = tp_match.group(1).replace(",", "")
        try:
            extracted["third_party_liability_limit"] = float(val_str)
        except ValueError:
            pass

    # Annual Premium
    prem_match = re.search(r"Annual Premium\s*[:|-]?\s*[■₹\$]?\s*([0-9,]+(?:\.[0-9]{2})?)", full_text, re.IGNORECASE)
    if prem_match:
        val_str = prem_match.group(1).replace(",", "")
        try:
            extracted["annual_premium"] = float(val_str)
        except ValueError:
            pass

    # Policy Period (Start Date & End Date)
    period_match = re.search(r"Policy Period\s*[:|-]?\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})\s+to\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", full_text, re.IGNORECASE)
    if period_match:
        s_date = _parse_date_str(period_match.group(1))
        e_date = _parse_date_str(period_match.group(2))
        if s_date: extracted["start_date"] = s_date
        if e_date: extracted["end_date"] = e_date

    # Customer Name / Email / Phone
    holder_match = re.search(r"Policyholder\s*[:|-]?\s*([A-Za-z\s.-]{2,35})", full_text, re.IGNORECASE)
    if holder_match:
        extracted["customer_name"] = holder_match.group(1).strip().split("\n")[0]

    email_match = re.search(r"Email\s*[:|-]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", full_text, re.IGNORECASE)
    if email_match:
        extracted["customer_email"] = email_match.group(1).strip()

    phone_match = re.search(r"Phone\s*[:|-]?\s*(\+?[0-9\s-]{8,20})", full_text, re.IGNORECASE)
    if phone_match:
        extracted["customer_phone"] = phone_match.group(1).strip()

    # Vehicle / Registration / Chassis details
    reg_match = re.search(r"Registration Number\s*[:|-]?\s*([A-Z0-9-]+)", full_text, re.IGNORECASE)
    if reg_match:
        extracted["registration_number"] = reg_match.group(1).strip().upper()

    veh_match = re.search(r"(?:Insured Vehicle|Vehicle)\s*[:|-]?\s*([A-Za-z0-9\s-]+)", full_text, re.IGNORECASE)
    if veh_match:
        val = veh_match.group(1).strip().split("\n")[0]
        if val.lower() != "information":
            extracted["vehicle_model"] = val

    vin_match = re.search(r"(?:VIN / Chassis Reference|Chassis Reference|VIN)\s*[:|-]?\s*([A-Z0-9]+)", full_text, re.IGNORECASE)
    if vin_match:
        extracted["chassis_number"] = vin_match.group(1).strip().upper()

    return extracted


async def verify_policy(
    db: AsyncSession,
    policy_number: str,
    incident_date: Optional[str] = None
) -> dict:
    from datetime import datetime
    from sqlalchemy.orm import selectinload
    from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
    from app.models.customer import Customer

    clean_pol = policy_number.strip()

    # 1. Parameterized SQL query loading Policy & Customer
    stmt = (
        select(Policy)
        .options(selectinload(Policy.customer))
        .where(Policy.policy_number == clean_pol)
    )
    res = await db.execute(stmt)
    policy = res.scalar_one_or_none()

    # 2. Check matching KnowledgeDocument in Knowledge Base for this policy_number
    active_kdocs = []
    try:
        kdoc_stmt = select(KnowledgeDocument).where(
            (
                (KnowledgeDocument.policy_number == clean_pol) |
                (KnowledgeDocument.title == clean_pol) |
                (KnowledgeDocument.source_file == clean_pol) |
                (KnowledgeDocument.title.ilike(f"%{clean_pol}%")) |
                (KnowledgeDocument.source_file.ilike(f"%{clean_pol}%"))
            ) & (KnowledgeDocument.is_active == True)
        )
        kdoc_res = await db.execute(kdoc_stmt)
        active_kdocs = list(kdoc_res.scalars().all())
    except Exception as kerr:
        logger.warning(f"verify_policy: KnowledgeDocument lookup warning: {kerr}")
        active_kdocs = []

    matching_kdoc = active_kdocs[0] if active_kdocs else None
    doc_extracted = {}

    if matching_kdoc:
        if not matching_kdoc.policy_number:
            matching_kdoc.policy_number = clean_pol

        # Read text from document chunks to dynamically extract exact policy numbers, limits, deductibles, dates
        chunk_stmt = select(KnowledgeChunk).where(KnowledgeChunk.document_id == matching_kdoc.id)
        chunk_res = await db.execute(chunk_stmt)
        chunks = chunk_res.scalars().all()
        full_doc_text = f"{matching_kdoc.title}\n{matching_kdoc.source_file or ''}\n" + "\n".join([c.content for c in chunks])
        doc_extracted = _extract_policy_details_from_text(full_doc_text)

        # Merge document metadata if present
        meta = matching_kdoc.metadata_json or {}
        if isinstance(meta, dict):
            for k, v in meta.items():
                if k not in doc_extracted and v:
                    doc_extracted[k] = v

    if not policy:
        if matching_kdoc:
            cust_name = doc_extracted.get("customer_name")
            cust_email = doc_extracted.get("customer_email")

            target_cust = None
            if cust_email:
                cres = await db.execute(select(Customer).where(Customer.email == cust_email))
                target_cust = cres.scalar_one_or_none()
            if not target_cust and cust_name:
                cres = await db.execute(select(Customer).where(Customer.name.ilike(f"%{cust_name}%")))
                target_cust = cres.scalar_one_or_none()

            if target_cust:
                category = doc_extracted.get("category", "Vehicle")
                cov_limit = doc_extracted.get("coverage_limit", 50000.00)
                deductible = doc_extracted.get("deductible", 500.00)
                s_date = doc_extracted.get("start_date", "2025-01-01")
                e_date = doc_extracted.get("end_date", "2027-12-31")

                policy = Policy(
                    policy_number=clean_pol,
                    category=category,
                    start_date=s_date,
                    end_date=e_date,
                    premium_status="Paid",
                    coverage_limit=cov_limit,
                    deductible=deductible,
                    active_claims_count=0,
                    customer_id=target_cust.id
                )
                db.add(policy)
                await db.commit()
                logger.info(f"Auto-synced Policy '{clean_pol}' into PostgreSQL for customer '{target_cust.name}' from KnowledgeDocument '{matching_kdoc.title}'")

                stmt = (
                    select(Policy)
                    .options(selectinload(Policy.customer))
                    .where(Policy.policy_number == clean_pol)
                )
                res = await db.execute(stmt)
                policy = res.scalar_one_or_none()

    if not policy:
        return {
            "status": "policy_not_found",
            "policy_number": policy_number,
            "policy_exists": False,
            "is_active": False,
            "is_expired": False,
            "issues": [f"Policy number '{policy_number}' was not found in PostgreSQL database."],
            "warnings": ["Verification failed: Unrecognized policy number."]
        }

    # Dynamically update policy record in PostgreSQL if extracted values from the document differ from DB
    updated_fields = False
    if doc_extracted:
        if "coverage_limit" in doc_extracted and float(policy.coverage_limit) != float(doc_extracted["coverage_limit"]):
            policy.coverage_limit = doc_extracted["coverage_limit"]
            updated_fields = True
        if "deductible" in doc_extracted and float(policy.deductible) != float(doc_extracted["deductible"]):
            policy.deductible = doc_extracted["deductible"]
            updated_fields = True
        if "start_date" in doc_extracted and policy.start_date != doc_extracted["start_date"]:
            policy.start_date = doc_extracted["start_date"]
            updated_fields = True
        if "end_date" in doc_extracted and policy.end_date != doc_extracted["end_date"]:
            policy.end_date = doc_extracted["end_date"]
            updated_fields = True
        if "category" in doc_extracted and policy.category != doc_extracted["category"]:
            policy.category = doc_extracted["category"]
            updated_fields = True

    if updated_fields:
        db.add(policy)
        await db.commit()
        logger.info(f"Updated Policy '{clean_pol}' in PostgreSQL with extracted document parameters: limit={policy.coverage_limit}, deductible={policy.deductible}")

    issues = []
    warnings = []
    is_active = True
    is_expired = False

    # Check 1: Premium Status
    if policy.premium_status not in ["Paid", "Active"]:
        is_active = False
        issues.append(f"Policy premium status is '{policy.premium_status}'. Overdue premium payment required.")

    # Check 2: Date Validity (Expired?)
    check_date_str = incident_date or datetime.now().strftime("%Y-%m-%d")
    try:
        start_dt = datetime.strptime(policy.start_date[:10], "%Y-%m-%d")
        end_dt = datetime.strptime(policy.end_date[:10], "%Y-%m-%d")
        check_dt = datetime.strptime(check_date_str[:10], "%Y-%m-%d")

        if check_dt < start_dt:
            is_active = False
            issues.append(f"Incident date '{check_date_str}' is prior to policy start date '{policy.start_date}'.")
        elif check_dt > end_dt:
            is_active = False
            is_expired = True
            issues.append(f"Policy expired on '{policy.end_date}'. Incident date '{check_date_str}' is outside coverage period.")
    except Exception as date_err:
        warnings.append(f"Date format parsing note: {str(date_err)}")

    doc_available = len(active_kdocs) > 0
    doc_id = active_kdocs[0].id if doc_available else None
    doc_title = active_kdocs[0].title if doc_available else None

    if not doc_available:
        warnings.append(f"No customer-specific policy document (PDF/terms) is currently ingested in Knowledge Base for policy '{clean_pol}'.")

    specific_details = dict(doc_extracted)
    currency = "INR"

    if is_expired:
        status = "policy_expired"
    elif not is_active:
        status = "policy_inactive"
    elif not doc_available:
        status = "policy_document_unavailable"
    else:
        status = "policy_found"

    cust = policy.customer

    return {
        "status": status,
        "policy_number": policy.policy_number,
        "policy_exists": True,
        "is_active": is_active,
        "is_expired": is_expired,
        "category": policy.category,
        "start_date": policy.start_date,
        "end_date": policy.end_date,
        "premium_status": policy.premium_status,
        "coverage_limit": float(policy.coverage_limit) if policy.coverage_limit else 0.0,
        "deductible": float(policy.deductible) if policy.deductible else 0.0,
        "currency": currency,
        "customer_id": policy.customer_id,
        "customer_name": cust.name if cust else None,
        "customer_email": cust.email if cust else None,
        "customer_phone": cust.phone if cust else None,
        "specific_details": specific_details,
        "policy_document_available": doc_available,
        "policy_document_id": doc_id,
        "policy_document_title": doc_title,
        "issues": issues,
        "warnings": warnings
    }

