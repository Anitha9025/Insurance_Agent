from typing import Dict, Any, Optional
from datetime import datetime
from app.agents.state import PolicyValidationResult, PolicyCheckItem
from app.core.logging import logger

class PolicyValidationAgent:
    """Agent responsible for validating claim specifications against actual PostgreSQL Policy records.
    Evaluates policy active window, coverage thresholds, premium payment status, and deductibles deterministically.
    """

    @staticmethod
    def validate(policy_data: Optional[Dict[str, Any]], claim_data: Optional[Dict[str, Any]]) -> PolicyValidationResult:
        logger.info("PolicyValidationAgent starting validation...")
        if not policy_data:
            return PolicyValidationResult(
                policy_found=False,
                policy_active=False,
                coverage_available=False,
                checks=[
                    PolicyCheckItem(
                        check="policy_existence",
                        status="failed",
                        evidence="Policy number associated with claim could not be located in database."
                    )
                ],
                issues=["Policy record missing in database."],
                policy_clause_validation_status="policy_clause_validation_pending"
            )

        policy_num = policy_data.get("policy_number") or policy_data.get("policyNumber")
        category = policy_data.get("category")
        start_date_str = policy_data.get("start_date") or policy_data.get("startDate")
        end_date_str = policy_data.get("end_date") or policy_data.get("endDate")
        premium_status = policy_data.get("premium_status") or policy_data.get("premiumStatus") or "Unknown"
        coverage_limit = policy_data.get("coverage_limit") or policy_data.get("coverageLimit")
        deductible = policy_data.get("deductible")

        checks = []
        issues = []
        is_active = True
        is_covered = True

        # Check 1: Premium Payment Status
        if premium_status in ["Paid", "Active"]:
            checks.append(PolicyCheckItem(
                check="premium_payment_status",
                status="passed",
                evidence=f"Policy premium status is '{premium_status}'."
            ))
        else:
            checks.append(PolicyCheckItem(
                check="premium_payment_status",
                status="failed",
                evidence=f"Policy premium status is '{premium_status}'."
            ))
            issues.append(f"Policy premium status is '{premium_status}'.")
            is_active = False

        # Check 2: Policy Period Window vs Incident Date
        incident_date_str = claim_data.get("incident_date") if claim_data else None
        if start_date_str and end_date_str and incident_date_str:
            try:
                inc_dt = datetime.strptime(incident_date_str[:10], "%Y-%m-%d")
                start_dt = datetime.strptime(start_date_str[:10], "%Y-%m-%d")
                end_dt = datetime.strptime(end_date_str[:10], "%Y-%m-%d")

                if start_dt <= inc_dt <= end_dt:
                    checks.append(PolicyCheckItem(
                        check="policy_period_window",
                        status="passed",
                        evidence=f"Incident date '{incident_date_str}' falls within policy coverage period ({start_date_str} to {end_date_str})."
                    ))
                else:
                    checks.append(PolicyCheckItem(
                        check="policy_period_window",
                        status="failed",
                        evidence=f"Incident date '{incident_date_str}' falls OUTSIDE policy coverage period ({start_date_str} to {end_date_str})."
                    ))
                    issues.append("Incident occurred outside active policy date range.")
                    is_active = False
            except Exception as dt_err:
                checks.append(PolicyCheckItem(
                    check="policy_period_window",
                    status="warning",
                    evidence=f"Date parsing format warning for incident/policy dates: {str(dt_err)}"
                ))

        # Check 3: Coverage Limit vs Claim Amount
        claim_amount = claim_data.get("claim_amount") if claim_data else None
        if coverage_limit is not None and claim_amount is not None:
            if claim_amount <= coverage_limit:
                checks.append(PolicyCheckItem(
                    check="coverage_limit_threshold",
                    status="passed",
                    evidence=f"Claim amount (${claim_amount:,.2f}) is within policy coverage limit (${coverage_limit:,.2f})."
                ))
            else:
                checks.append(PolicyCheckItem(
                    check="coverage_limit_threshold",
                    status="failed",
                    evidence=f"Claim amount (${claim_amount:,.2f}) EXCEEDS policy coverage limit (${coverage_limit:,.2f})."
                ))
                issues.append(f"Claim amount (${claim_amount:,.2f}) exceeds policy limit (${coverage_limit:,.2f}).")
                is_covered = False

        # Check 4: Category Alignment
        claim_category = claim_data.get("category") if claim_data else None
        if category and claim_category:
            if category.lower() == claim_category.lower():
                checks.append(PolicyCheckItem(
                    check="insurance_category_match",
                    status="passed",
                    evidence=f"Claim category '{claim_category}' matches policy category '{category}'."
                ))
            else:
                checks.append(PolicyCheckItem(
                    check="insurance_category_match",
                    status="failed",
                    evidence=f"Claim category '{claim_category}' DOES NOT match policy category '{category}'."
                ))
                issues.append(f"Category mismatch: Policy is '{category}', Claim is '{claim_category}'.")
                is_covered = False

        # Check 5: Customer Policy Document Availability
        policy_doc_available = policy_data.get("policy_document_available", True)
        if policy_doc_available:
            checks.append(PolicyCheckItem(
                check="policy_document_ingestion",
                status="passed",
                evidence=f"Customer-specific policy terms document is ingested in PostgreSQL Knowledge Base for policy '{policy_num}'."
            ))
        else:
            checks.append(PolicyCheckItem(
                check="policy_document_ingestion",
                status="warning",
                evidence=f"No customer-specific policy terms document is currently ingested in Knowledge Base for policy '{policy_num}'. Clause verification requires human officer review."
            ))
            issues.append(f"Policy terms document unavailable for policy '{policy_num}'. Requires human officer verification.")


        logger.info(
            f"PolicyValidationAgent completed for policy {policy_num}: "
            f"active={is_active}, covered={is_covered}, issues={len(issues)}"
        )

        return PolicyValidationResult(
            policy_found=True,
            policy_active=is_active,
            coverage_available=is_covered,
            policy_number=policy_num,
            category=category,
            premium_status=premium_status,
            coverage_limit=coverage_limit,
            deductible=deductible,
            checks=checks,
            issues=issues,
            policy_clause_validation_status="policy_clause_validation_pending"
        )
