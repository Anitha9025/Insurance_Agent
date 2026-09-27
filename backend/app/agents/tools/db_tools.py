from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.claim import Claim
from app.models.customer import Customer
from app.models.policy import Policy
from app.models.document import ClaimDocument, OCRField
from app.core.logging import logger

# ---------------------------------------------------------
# Strongly-Typed Pydantic Models for Tool Output
# ---------------------------------------------------------

class CustomerToolOutput(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    national_id: str
    address: str
    is_verified: bool
    risk_score: float

class PolicyToolOutput(BaseModel):
    id: str
    policy_number: str
    policy_type: str
    coverage_limit: float
    deductible: float
    start_date: str
    end_date: str
    status: str

class ClaimToolOutput(BaseModel):
    id: str
    claim_number: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    incident_date: str
    location: str
    claim_amount: float
    customer_id: str
    policy_number: str

class OCRFieldOutput(BaseModel):
    field_name: str
    extracted_value: str
    confidence: float

class DocumentToolOutput(BaseModel):
    id: str
    file_name: str
    category: str
    ocr_status: str
    verification_status: str
    ocr_fields: List[OCRFieldOutput] = Field(default_factory=list)

class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    error_message: Optional[str] = None
    data: Optional[Any] = None

# ---------------------------------------------------------
# Parameterized Controlled Database Tools
# ---------------------------------------------------------

async def get_claim_by_id(db: AsyncSession, claim_id: str) -> ToolExecutionResult:
    """Read-only retrieval of a claim record by ID."""
    tool_name = "get_claim_by_id"
    logger.info(f"[DB Tool Execution] Calling {tool_name} with claim_id={claim_id}")
    try:
        stmt = select(Claim).where(Claim.id == claim_id)
        res = await db.execute(stmt)
        claim = res.scalar_one_or_none()
        if not claim:
            return ToolExecutionResult(tool_name=tool_name, success=False, error_message=f"Claim '{claim_id}' not found.")
        
        output = ClaimToolOutput(
            id=claim.id,
            claim_number=claim.claim_number,
            title=claim.title,
            description=claim.description,
            category=claim.category,
            priority=claim.priority,
            status=claim.status,
            incident_date=claim.incident_date,
            location=claim.location,
            claim_amount=float(claim.claim_amount or 0.0),
            customer_id=claim.customer_id,
            policy_number=claim.policy_number
        )
        return ToolExecutionResult(tool_name=tool_name, success=True, data=output.model_dump())
    except Exception as e:
        logger.error(f"[DB Tool Error] {tool_name} failed: {e}")
        return ToolExecutionResult(tool_name=tool_name, success=False, error_message=str(e))

async def get_customer_by_id(db: AsyncSession, customer_id: str) -> ToolExecutionResult:
    """Read-only retrieval of a customer record by ID."""
    tool_name = "get_customer_by_id"
    logger.info(f"[DB Tool Execution] Calling {tool_name} with customer_id={customer_id}")
    try:
        stmt = select(Customer).where(Customer.id == customer_id)
        res = await db.execute(stmt)
        cust = res.scalar_one_or_none()
        if not cust:
            return ToolExecutionResult(tool_name=tool_name, success=False, error_message=f"Customer '{customer_id}' not found.")
        
        output = CustomerToolOutput(
            id=cust.id,
            name=cust.name,
            email=cust.email,
            phone=cust.phone,
            national_id=cust.national_id,
            address=cust.address,
            is_verified=cust.is_verified,
            risk_score=float(cust.risk_score or 0.0)
        )
        return ToolExecutionResult(tool_name=tool_name, success=True, data=output.model_dump())
    except Exception as e:
        logger.error(f"[DB Tool Error] {tool_name} failed: {e}")
        return ToolExecutionResult(tool_name=tool_name, success=False, error_message=str(e))

async def get_policy_by_number(db: AsyncSession, policy_number: str) -> ToolExecutionResult:
    """Read-only retrieval of policy details by policy number."""
    tool_name = "get_policy_by_number"
    logger.info(f"[DB Tool Execution] Calling {tool_name} with policy_number={policy_number}")
    try:
        stmt = select(Policy).where(Policy.policy_number == policy_number)
        res = await db.execute(stmt)
        pol = res.scalar_one_or_none()
        if not pol:
            return ToolExecutionResult(tool_name=tool_name, success=False, error_message=f"Policy '{policy_number}' not found.")
        
        output = PolicyToolOutput(
            id=pol.id,
            policy_number=pol.policy_number,
            policy_type=pol.policy_type,
            coverage_limit=float(pol.coverage_limit or 0.0),
            deductible=float(pol.deductible or 0.0),
            start_date=pol.start_date,
            end_date=pol.end_date,
            status=pol.status
        )
        return ToolExecutionResult(tool_name=tool_name, success=True, data=output.model_dump())
    except Exception as e:
        logger.error(f"[DB Tool Error] {tool_name} failed: {e}")
        return ToolExecutionResult(tool_name=tool_name, success=False, error_message=str(e))

async def get_customer_claims_history(db: AsyncSession, customer_id: str, exclude_claim_id: Optional[str] = None) -> ToolExecutionResult:
    """Read-only retrieval of historical claims for a given customer."""
    tool_name = "get_customer_claims_history"
    logger.info(f"[DB Tool Execution] Calling {tool_name} with customer_id={customer_id}")
    try:
        stmt = select(Claim).where(Claim.customer_id == customer_id)
        if exclude_claim_id:
            stmt = stmt.where(Claim.id != exclude_claim_id)
        res = await db.execute(stmt)
        claims = res.scalars().all()
        
        history = []
        for c in claims:
            history.append(ClaimToolOutput(
                id=c.id,
                claim_number=c.claim_number,
                title=c.title,
                description=c.description,
                category=c.category,
                priority=c.priority,
                status=c.status,
                incident_date=c.incident_date,
                location=c.location,
                claim_amount=float(c.claim_amount or 0.0),
                customer_id=c.customer_id,
                policy_number=c.policy_number
            ).model_dump())

        return ToolExecutionResult(tool_name=tool_name, success=True, data={"total_claims": len(history), "claims": history})
    except Exception as e:
        logger.error(f"[DB Tool Error] {tool_name} failed: {e}")
        return ToolExecutionResult(tool_name=tool_name, success=False, error_message=str(e))

async def get_claim_documents(db: AsyncSession, claim_id: str) -> ToolExecutionResult:
    """Read-only retrieval of uploaded documents and extracted OCR fields for a claim."""
    tool_name = "get_claim_documents"
    logger.info(f"[DB Tool Execution] Calling {tool_name} with claim_id={claim_id}")
    try:
        stmt = select(ClaimDocument).where(ClaimDocument.claim_id == claim_id)
        res = await db.execute(stmt)
        docs = res.scalars().all()

        docs_list = []
        for doc in docs:
            ocr_stmt = select(OCRField).where(OCRField.document_id == doc.id)
            ocr_res = await db.execute(ocr_stmt)
            ocr_fields = ocr_res.scalars().all()

            doc_output = DocumentToolOutput(
                id=doc.id,
                file_name=doc.file_name,
                category=doc.category,
                ocr_status=doc.ocr_status,
                verification_status=doc.verification_status,
                ocr_fields=[
                    OCRFieldOutput(
                        field_name=f.field_name,
                        extracted_value=f.extracted_value,
                        confidence=float(f.confidence or 0.0)
                    ) for f in ocr_fields
                ]
            )
            docs_list.append(doc_output.model_dump())

        return ToolExecutionResult(tool_name=tool_name, success=True, data=docs_list)
    except Exception as e:
        logger.error(f"[DB Tool Error] {tool_name} failed: {e}")
        return ToolExecutionResult(tool_name=tool_name, success=False, error_message=str(e))
