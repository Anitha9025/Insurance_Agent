"""
Evidence Normalization Agent — Phase 7
Converts all Phase 1–6 agent outputs into a flat list of neutral, source-attributed EvidenceItem objects.
Language is always factual. No fraud labels are applied at this stage.
"""
from typing import List, Optional, Dict, Any
from app.agents.state import (
    ClaimWorkflowState,
    EvidenceItem,
    IntakeAgentResult,
    CustomerVerificationResult,
    DocumentAnalysisResult,
    PolicyValidationResult,
    ClaimHistoryResult,
)
from app.core.logging import logger


class EvidenceNormalizationAgent:
    """Normalizes all prior agent results into a structured EvidenceItem list.
    Does not add fraud labels. Only classifies evidence as observed / inferred / unknown.
    """

    @staticmethod
    def normalize(state: ClaimWorkflowState) -> List[EvidenceItem]:
        logger.info(f"EvidenceNormalizationAgent: Normalizing evidence for claim {state.claim_id}")
        evidence_items: List[EvidenceItem] = []
        counter = 0

        def _next_id() -> str:
            nonlocal counter
            counter += 1
            return f"ev-{counter:03d}"

        # ── 1. INTAKE AGENT EVIDENCE ──────────────────────────────────────────
        intake = state.intake_analysis
        if intake:
            if intake.claim_data_available:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Claim Intake Agent",
                    evidence_type="general_observation",
                    category="observed",
                    description=f"Claim record exists in database. Type: {intake.claim_type or 'Unknown'}. Amount: ${intake.claim_amount:,.2f}." if intake.claim_amount else f"Claim record exists. Type: {intake.claim_type or 'Unknown'}.",
                    field_name="claim_record",
                    observed_value="present",
                    severity="info"
                ))
            else:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Claim Intake Agent",
                    evidence_type="general_observation",
                    category="observed",
                    description="Claim record not found in database.",
                    field_name="claim_record",
                    observed_value="missing",
                    severity="high"
                ))

            for missing in intake.missing_information:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Claim Intake Agent",
                    evidence_type="missing_document",
                    category="observed",
                    description=f"Required intake field or document is missing: '{missing}'.",
                    field_name=missing,
                    severity="medium"
                ))

        # ── 2. CUSTOMER VERIFICATION EVIDENCE ─────────────────────────────────
        cust = state.customer_verification
        if cust:
            if cust.customer_found and cust.verified:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Customer Verification Agent",
                    evidence_type="customer_verified",
                    category="observed",
                    description=f"Customer identity verified. Matched fields: {', '.join(cust.matched_fields)}.",
                    field_name="customer_identity",
                    observed_value="verified",
                    severity="info"
                ))
            elif cust.customer_found and not cust.verified:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Customer Verification Agent",
                    evidence_type="customer_mismatch",
                    category="observed",
                    description=f"Customer record found but verification failed. Mismatches in: {', '.join([m.field for m in cust.mismatches]) if cust.mismatches else 'unknown fields'}.",
                    field_name="customer_identity",
                    observed_value="unverified",
                    severity="medium"
                ))
                for mismatch in cust.mismatches:
                    evidence_items.append(EvidenceItem(
                        evidence_id=_next_id(),
                        source_agent="Customer Verification Agent",
                        evidence_type="customer_mismatch",
                        category="observed",
                        description=f"Field '{mismatch.field}' mismatch: claim registered value is '{mismatch.claim_value}', database record value is '{mismatch.database_value}'.",
                        field_name=mismatch.field,
                        observed_value=mismatch.claim_value or "not provided",
                        expected_value=mismatch.database_value or "not on record",
                        severity="medium"
                    ))
            elif not cust.customer_found:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Customer Verification Agent",
                    evidence_type="customer_mismatch",
                    category="observed",
                    description="Customer record not found in database. Customer identity cannot be verified.",
                    field_name="customer_record",
                    observed_value="not found",
                    severity="high"
                ))

        # ── 3. DOCUMENT ANALYSIS EVIDENCE ─────────────────────────────────────
        doc = state.document_analysis
        if doc:
            if doc.documents_analyzed == 0:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Document Analysis Agent",
                    evidence_type="missing_document",
                    category="observed",
                    description="No documents were attached to this claim for analysis.",
                    field_name="documents",
                    observed_value="0 documents",
                    severity="medium"
                ))
            else:
                # Per-document evidence
                for d in doc.documents:
                    if d.verification_status == "Flagged":
                        evidence_items.append(EvidenceItem(
                            evidence_id=_next_id(),
                            source_agent="Document Analysis Agent",
                            evidence_type="document_mismatch",
                            category="observed",
                            description=f"Document '{d.filename}' (ID: {d.document_id}) has been flagged for human review during verification.",
                            field_name="verification_status",
                            source_document_id=d.document_id,
                            observed_value="Flagged",
                            severity="medium"
                        ))
                    elif d.verification_status == "Verified":
                        evidence_items.append(EvidenceItem(
                            evidence_id=_next_id(),
                            source_agent="Document Analysis Agent",
                            evidence_type="document_verified",
                            category="observed",
                            description=f"Document '{d.filename}' verified with {d.extracted_fields_count} OCR fields extracted.",
                            field_name="verification_status",
                            source_document_id=d.document_id,
                            observed_value="Verified",
                            severity="info"
                        ))

                # Aggregated textual/visual evidence
                for ev_text in doc.evidence[:5]:
                    evidence_items.append(EvidenceItem(
                        evidence_id=_next_id(),
                        source_agent="Document Analysis Agent",
                        evidence_type="general_observation",
                        category="observed",
                        description=ev_text,
                        severity="info"
                    ))

                # Document mismatches from uncertainties
                for uncertainty in doc.uncertainties:
                    u_lower = uncertainty.lower()
                    if "name spell check warning" in u_lower:
                        ev_type = "customer_name_spelling_variation"
                        sev = "medium"
                    elif "customer name mismatch" in u_lower:
                        ev_type = "customer_name_mismatch"
                        sev = "high"
                    elif "email mismatch" in u_lower:
                        ev_type = "email_mismatch"
                        sev = "medium"
                    elif "phone mismatch" in u_lower:
                        ev_type = "phone_mismatch"
                        sev = "medium"
                    elif "policy number mismatch" in u_lower:
                        ev_type = "policy_number_mismatch"
                        sev = "high"
                    elif "vehicle registration spell check warning" in u_lower:
                        ev_type = "vehicle_registration_spelling_variation"
                        sev = "medium"
                    elif "vehicle registration mismatch" in u_lower:
                        ev_type = "vehicle_registration_mismatch"
                        sev = "high"
                    elif "chassis number spell check warning" in u_lower:
                        ev_type = "chassis_number_spelling_variation"
                        sev = "medium"
                    elif "chassis number mismatch" in u_lower:
                        ev_type = "chassis_number_mismatch"
                        sev = "high"
                    elif "incident date mismatch" in u_lower:
                        ev_type = "incident_date_mismatch"
                        sev = "medium"
                    elif "mismatch" in u_lower:
                        ev_type = "document_mismatch"
                        sev = "medium"
                    elif "visual" in u_lower:
                        ev_type = "vision_conflict"
                        sev = "low"
                    else:
                        ev_type = "general_observation"
                        sev = "low"

                    evidence_items.append(EvidenceItem(
                        evidence_id=_next_id(),
                        source_agent="Document Analysis Agent",
                        evidence_type=ev_type,
                        category="inferred" if ev_type == "general_observation" else "observed",
                        description=uncertainty,
                        severity=sev
                    ))

        # ── 4. POLICY VALIDATION EVIDENCE ─────────────────────────────────────
        pol = state.policy_validation
        if pol:
            if not pol.policy_found:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Policy Validation Agent",
                    evidence_type="general_observation",
                    category="observed",
                    description="No policy record was found in the database for this claim.",
                    field_name="policy_record",
                    observed_value="not found",
                    severity="high"
                ))
            else:
                # Premium status
                if pol.premium_status not in ["Paid", "Active"]:
                    evidence_items.append(EvidenceItem(
                        evidence_id=_next_id(),
                        source_agent="Policy Validation Agent",
                        evidence_type="premium_lapsed",
                        category="observed",
                        description=f"Policy premium status is '{pol.premium_status}', indicating the policy may not be current.",
                        field_name="premium_status",
                        observed_value=pol.premium_status,
                        expected_value="Paid or Active",
                        severity="high"
                    ))
                else:
                    evidence_items.append(EvidenceItem(
                        evidence_id=_next_id(),
                        source_agent="Policy Validation Agent",
                        evidence_type="policy_active",
                        category="observed",
                        description=f"Policy premium status is '{pol.premium_status}'. Policy is current.",
                        field_name="premium_status",
                        observed_value=pol.premium_status,
                        severity="info"
                    ))

                for check in pol.checks:
                    if check.status == "failed":
                        ev_type_map = {
                            "policy_period_window": "policy_period_violation",
                            "coverage_limit_threshold": "coverage_exceeded",
                            "insurance_category_match": "category_mismatch",
                        }
                        ev_type = ev_type_map.get(check.check, "general_observation")
                        evidence_items.append(EvidenceItem(
                            evidence_id=_next_id(),
                            source_agent="Policy Validation Agent",
                            evidence_type=ev_type,
                            category="observed",
                            description=check.evidence,
                            field_name=check.check,
                            observed_value="failed",
                            severity="high"
                        ))
                    elif check.status == "passed":
                        evidence_items.append(EvidenceItem(
                            evidence_id=_next_id(),
                            source_agent="Policy Validation Agent",
                            evidence_type="coverage_confirmed",
                            category="observed",
                            description=check.evidence,
                            field_name=check.check,
                            observed_value="passed",
                            severity="info"
                        ))

        # ── 5. CLAIM HISTORY EVIDENCE ──────────────────────────────────────────
        hist = state.claim_history
        if hist:
            if hist.total_previous_claims == 0:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Claim History Agent",
                    evidence_type="claim_history_normal",
                    category="observed",
                    description="No prior claims found for this customer. First-time claimant.",
                    field_name="total_previous_claims",
                    observed_value="0",
                    severity="info"
                ))
            else:
                severity = "low" if hist.total_previous_claims < 5 else "medium"
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Claim History Agent",
                    evidence_type="claim_history_pattern",
                    category="observed",
                    description=f"Customer has {hist.total_previous_claims} prior claim(s). Approved: {hist.approved_claims_count}, Rejected: {hist.rejected_claims_count}. Total historical amount: ${hist.total_previous_claim_amount:,.2f}.",
                    field_name="claim_history",
                    observed_value=str(hist.total_previous_claims),
                    severity=severity
                ))
                if hist.rejected_claims_count > 0 and hist.total_previous_claims > 0:
                    rejection_rate = hist.rejected_claims_count / hist.total_previous_claims
                    if rejection_rate >= 0.5:
                        evidence_items.append(EvidenceItem(
                            evidence_id=_next_id(),
                            source_agent="Claim History Agent",
                            evidence_type="claim_history_pattern",
                            category="inferred",
                            description=f"Observed rejection rate is {rejection_rate:.0%} ({hist.rejected_claims_count} of {hist.total_previous_claims} prior claims). This is a factual historical pattern; context may vary.",
                            field_name="rejection_rate",
                            observed_value=f"{rejection_rate:.0%}",
                            severity="medium"
                        ))

        # ── 6. RAG KNOWLEDGE EVIDENCE ──────────────────────────────────────────
        rag = state.rag_analysis
        if rag:
            is_grounded = rag.get("is_grounded", False)
            citations = rag.get("citations", [])
            uncertainty = rag.get("uncertainty_flag", False)
            if is_grounded and citations:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="RAG Knowledge Agent",
                    evidence_type="general_observation",
                    category="observed",
                    description=f"Policy knowledge base retrieved {len(citations)} relevant clause(s). Knowledge retrieval is grounded.",
                    field_name="rag_citations",
                    observed_value=str(len(citations)),
                    severity="info"
                ))
            if uncertainty:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="RAG Knowledge Agent",
                    evidence_type="rag_clause_unavailable",
                    category="unknown",
                    description="Policy knowledge retrieval returned low-confidence results. Clause validation may be incomplete.",
                    field_name="rag_confidence",
                    severity="low"
                ))

        # ── 7. MEMORY AGENT EVIDENCE ───────────────────────────────────────────
        mem = state.retrieved_memories
        if mem:
            count = mem.get("similar_claims_count", 0)
            if count > 0:
                evidence_items.append(EvidenceItem(
                    evidence_id=_next_id(),
                    source_agent="Memory Agent",
                    evidence_type="general_observation",
                    category="inferred",
                    description=f"Memory system retrieved {count} similar historical claim decision(s) as precedent context.",
                    field_name="similar_claims_count",
                    observed_value=str(count),
                    severity="info"
                ))

        logger.info(
            f"EvidenceNormalizationAgent: Produced {len(evidence_items)} evidence items for claim {state.claim_id}"
        )
        return evidence_items
