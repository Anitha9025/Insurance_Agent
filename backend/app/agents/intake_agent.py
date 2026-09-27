from typing import List, Dict, Any, Optional
from app.agents.state import IntakeAgentResult
from app.core.logging import logger

class ClaimIntakeAgent:
    """Agent responsible for inspecting and validating the completeness of raw claim data
    retrieved directly from the database.
    Ensures zero hallucination and reports missing fields or structural data gaps.
    """

    @staticmethod
    def analyze(claim_data: Optional[Dict[str, Any]], documents_data: Optional[List[Dict[str, Any]]] = None) -> IntakeAgentResult:
        logger.info("ClaimIntakeAgent starting analysis...")
        if not claim_data:
            return IntakeAgentResult(
                claim_id="unknown",
                claim_data_available=False,
                missing_information=["Claim record not found in database"],
                warnings=["Cannot process claim intake: Database record missing."]
            )

        claim_id = claim_data.get("id") or claim_data.get("claim_id") or "unknown"
        claim_type = claim_data.get("category")
        claim_amount = claim_data.get("claim_amount")
        incident_date = claim_data.get("incident_date")
        description = claim_data.get("description")
        docs = documents_data if documents_data is not None else (claim_data.get("documents", []) or [])

        missing_fields = []
        warnings = []

        # Validate core claim attributes
        if not claim_data.get("customer_id"):
            missing_fields.append("customer_id")
        if not claim_data.get("policy_number"):
            missing_fields.append("policy_number")
        if not claim_type or claim_type == "unknown":
            missing_fields.append("category")
        if claim_amount is None or claim_amount <= 0:
            missing_fields.append("claim_amount")
        if not incident_date:
            missing_fields.append("incident_date")
        if not description or len(description.strip()) < 5:
            missing_fields.append("description")

        if len(docs) == 0:
            warnings.append("No supporting documents submitted with claim.")

        if claim_data.get("is_emergency"):
            warnings.append("Claim is marked for Emergency Escalation.")

        logger.info(f"ClaimIntakeAgent completed for claim {claim_id}: missing={missing_fields}, warnings={len(warnings)}")
        return IntakeAgentResult(
            claim_id=claim_id,
            claim_data_available=True,
            claim_type=claim_type,
            claim_amount=claim_amount,
            incident_date=incident_date,
            description=description,
            documents_submitted_count=len(docs),
            missing_information=missing_fields,
            warnings=warnings
        )
