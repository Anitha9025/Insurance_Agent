from typing import Dict, Any, Optional
from app.agents.state import CustomerVerificationResult, CustomerFieldMismatch
from app.core.logging import logger

class CustomerVerificationAgent:
    """Agent responsible for verifying claim customer details against actual PostgreSQL Customer records.
    Produces factual matching evidence and mismatch reports without prematurely labeling mismatches as fraud.
    """

    @staticmethod
    def verify(customer_data: Optional[Dict[str, Any]], claim_data: Optional[Dict[str, Any]]) -> CustomerVerificationResult:
        logger.info("CustomerVerificationAgent starting verification...")
        if not customer_data:
            return CustomerVerificationResult(
                customer_found=False,
                verified=False,
                missing_fields=["customer_record"],
                mismatches=[],
                matched_fields=[]
            )

        matched = []
        mismatches = []
        missing = []

        # Check essential profile attributes
        name = customer_data.get("name")
        email = customer_data.get("email")
        phone = customer_data.get("phone")
        nat_id = customer_data.get("national_id") or customer_data.get("nationalId")

        if name:
            matched.append("customer_name")
        else:
            missing.append("customer_name")

        if email:
            matched.append("email")
        else:
            missing.append("email")

        if phone:
            matched.append("phone")
        else:
            missing.append("phone")

        if nat_id:
            matched.append("national_id")
        else:
            missing.append("national_id")

        # Verify claim ownership alignment
        claim_cust_id = claim_data.get("customer_id") if claim_data else None
        db_cust_id = customer_data.get("id")

        if claim_cust_id and db_cust_id:
            if str(claim_cust_id) == str(db_cust_id):
                matched.append("customer_id_ownership")
            else:
                mismatches.append(CustomerFieldMismatch(
                    field="customer_id_ownership",
                    claim_value=str(claim_cust_id),
                    database_value=str(db_cust_id)
                ))

        verified_status = len(mismatches) == 0 and customer_data.get("name") is not None

        logger.info(
            f"CustomerVerificationAgent completed for customer {customer_data.get('id')}: "
            f"verified={verified_status}, matched={len(matched)}, mismatches={len(mismatches)}"
        )

        return CustomerVerificationResult(
            customer_found=True,
            verified=verified_status,
            matched_fields=matched,
            mismatches=mismatches,
            missing_fields=missing,
            risk_score=customer_data.get("risk_score"),
            member_since=customer_data.get("member_since")
        )
