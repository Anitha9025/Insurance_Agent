"""
Recommendation Agent — Phase 7
Produces an AI-assisted advisory recommendation for a claim.
Deterministic override rules take priority over LLM output.
LLM generates reasoning narrative grounded in actual evidence.
Officer always retains final decision authority.
"""
import time
from typing import List, Optional
from app.agents.state import (
    ClaimWorkflowState,
    EvidenceItem,
    FraudRiskAssessmentResult,
    RecommendationResult,
)
from app.core.cloud_llm import generate_text, generate_json
from app.core.config import settings
from app.core.logging import logger

PROMPT_VERSION = "v1.0"

# Human-readable labels for recommendation types
RECOMMENDATION_LABELS = {
    "approve_recommended":       "Approve Recommended",
    "reject_recommended":        "Reject Recommended",
    "request_more_information":  "Request Additional Information",
    "manual_review_required":    "Manual Review Required",
    "insufficient_evidence":     "Insufficient Evidence for Recommendation",
    "processing_failed":         "Processing Failed — Manual Review Required",
}


def _build_evidence_summary(evidence_items: List[EvidenceItem], max_items: int = 10) -> str:
    """Builds a compact text summary of evidence items for LLM prompting."""
    if not evidence_items:
        return "No evidence items available."
    lines = []
    for item in evidence_items[:max_items]:
        severity_tag = f"[{item.severity.upper()}]" if item.severity != "info" else ""
        lines.append(f"- {item.source_agent} | {item.evidence_type} | {item.category} {severity_tag}: {item.description}")
    if len(evidence_items) > max_items:
        lines.append(f"  ...and {len(evidence_items) - max_items} additional evidence items.")
    return "\n".join(lines)


def _build_fraud_summary(assessment: Optional[FraudRiskAssessmentResult]) -> str:
    if not assessment:
        return "Fraud risk assessment was not completed."
    lines = [
        f"Risk Level: {assessment.risk_level.upper()}",
        f"Composite Risk Score: {assessment.rule_based_score:.1f}/100",
        f"Signals Triggered: {assessment.signal_count}",
    ]
    for sig in assessment.signals[:6]:
        lines.append(f"  - Signal [{sig.severity.upper()}]: {sig.description}")
    return "\n".join(lines)


class RecommendationAgent:
    """Phase 7 Recommendation Agent.
    Deterministic override rules first, then LLM-grounded reasoning narrative.
    Never makes a final claim decision. Always advisory.
    """

    @staticmethod
    async def recommend(
        state: ClaimWorkflowState,
        evidence_items: List[EvidenceItem],
        assessment: FraudRiskAssessmentResult
    ) -> RecommendationResult:
        start_time = time.time()
        logger.info(f"RecommendationAgent: Building recommendation for claim {state.claim_id}...")

        recommendation_type: str = ""
        override_reason: Optional[str] = None
        confidence_basis: str = "evidence"
        policy_references: List[str] = []
        risk_summary: List[str] = []
        missing_information: List[str] = list(assessment.missing_information)
        required_next_actions: List[str] = []

        # ── STEP 1: Deterministic Override Rules ─────────────────────────────
        pol = state.policy_validation
        cust = state.customer_verification
        intake = state.intake_analysis
        doc = state.document_analysis

        # Override Rule 1: Policy period violation → reject_recommended
        if pol and pol.policy_found:
            if not pol.policy_active:
                recommendation_type = "reject_recommended"
                override_reason = "Deterministic override: Policy was not active at the time of the incident. Claim falls outside the covered period."
                required_next_actions.append("Verify incident date against policy dates using original documents.")

        # Override Rule 2: Premium unpaid/lapsed → reject_recommended
        if not recommendation_type and pol and pol.policy_found:
            if pol.premium_status not in ["Paid", "Active", None]:
                recommendation_type = "reject_recommended"
                override_reason = f"Deterministic override: Policy premium status is '{pol.premium_status}'. Coverage requires active premium payment."
                required_next_actions.append("Confirm premium payment receipts before reconsidering claim.")

        # Override Rule 3: Policy not found → manual_review_required
        if not recommendation_type and pol and not pol.policy_found:
            recommendation_type = "manual_review_required"
            override_reason = "Deterministic override: No policy record found in database. Cannot determine coverage."
            required_next_actions.append("Locate and verify policy documentation manually.")

        # Override Rule 4: Customer not found/unverified → manual_review_required
        if not recommendation_type and cust:
            if not cust.customer_found:
                recommendation_type = "manual_review_required"
                override_reason = "Deterministic override: Customer identity not found in database."
                required_next_actions.append("Verify customer identity with original identification documents.")

        # Override Rule 5: Category mismatch → manual_review_required
        if not recommendation_type and pol:
            for issue in (pol.issues or []):
                if "mismatch" in issue.lower() and "category" in issue.lower():
                    recommendation_type = "manual_review_required"
                    override_reason = f"Deterministic override: Claim category does not match policy category. Issue: {issue}"
                    required_next_actions.append("Verify claim category against policy coverage type.")
                    break

        # Override Rule 6: Missing critical documents → request_more_information
        if not recommendation_type and intake:
            if intake.missing_information and len(intake.missing_information) > 0:
                recommendation_type = "request_more_information"
                override_reason = f"Deterministic override: Required claim information is missing: {', '.join(intake.missing_information[:3])}."
                required_next_actions.extend([f"Obtain missing item: {m}" for m in intake.missing_information[:3]])

        if not recommendation_type and doc and doc.documents_analyzed == 0:
            recommendation_type = "request_more_information"
            override_reason = "Deterministic override: No supporting documents were submitted with this claim."
            required_next_actions.append("Request submission of all required supporting documents.")

        # Override Rule 7: Any high severity risk signals or score >= 20.0 → manual_review_required
        if not recommendation_type:
            signals_list = getattr(assessment, "signals", []) if not isinstance(assessment, dict) else assessment.get("signals", [])
            high_signals = [s for s in signals_list if (s.get("severity") if isinstance(s, dict) else getattr(s, "severity", None)) == "high"]
            score_val = getattr(assessment, "rule_based_score", 0.0) if not isinstance(assessment, dict) else assessment.get("rule_based_score", 0.0)
            r_level = getattr(assessment, "risk_level", "unknown") if not isinstance(assessment, dict) else assessment.get("risk_level", "unknown")

            if high_signals or score_val >= 20.0 or r_level in ("medium", "high", "critical"):
                recommendation_type = "manual_review_required"
                high_desc = ", ".join([s.get("signal_type") if isinstance(s, dict) else getattr(s, "signal_type", "") for s in high_signals[:3]]) if high_signals else f"Risk Score {score_val:.1f}"
                override_reason = f"Deterministic override: High severity risk signals or risk score >= 20 detected ({high_desc}). Requires manual officer review."
                required_next_actions.append("Examine flagged identity, policy, or document mismatches before deciding.")

        # Override Rule 8: RAG policy document unavailable → manual_review_required
        rag_state = state.rag_analysis
        if not recommendation_type and rag_state:
            if not rag_state.get("policy_document_available", True) or rag_state.get("coverage_status") == "policy_unavailable":
                recommendation_type = "manual_review_required"
                override_reason = "Deterministic override: Customer policy document unavailable in Knowledge Base. Coverage unverified."
                required_next_actions.append("Locate and verify customer policy terms document manually.")

        # Override Rule 9: No evidence available → insufficient_evidence
        if not recommendation_type and len(evidence_items) == 0:
            recommendation_type = "insufficient_evidence"
            override_reason = "Deterministic override: No evidence items available for recommendation."
            confidence_basis = "insufficient"

        # Override Rule 10: Default — if all deterministic checks pass → approve_recommended
        if not recommendation_type:
            score_val = getattr(assessment, "rule_based_score", 0.0) if not isinstance(assessment, dict) else assessment.get("rule_based_score", 0.0)
            r_level = getattr(assessment, "risk_level", "unknown") if not isinstance(assessment, dict) else assessment.get("risk_level", "unknown")
            if (
                pol and pol.policy_active and pol.coverage_available
                and cust and cust.verified
                and r_level in ("low", "unknown")
                and score_val < 20.0
            ):
                recommendation_type = "approve_recommended"
                confidence_basis = "evidence"
            else:
                recommendation_type = "manual_review_required"
                override_reason = "Deterministic fallback: Conditions for approve_recommended not fully met."

        if override_reason:
            confidence_basis = "override"
            logger.info(f"RecommendationAgent: Override applied → {recommendation_type}: {override_reason}")

        # ── STEP 2: Collect Policy References from RAG ─────────────────────────
        rag = state.rag_analysis
        if rag and rag.get("citations"):
            for cit in rag.get("citations", [])[:4]:
                if isinstance(cit, dict):
                    ref_text = cit.get("text") or cit.get("content") or str(cit)
                    if ref_text:
                        policy_references.append(f"Policy KB: {ref_text[:120]}")
                elif isinstance(cit, str):
                    policy_references.append(f"Policy KB: {cit[:120]}")

        # ── STEP 3: Risk Summary from Signals ──────────────────────────────────
        signals_list = getattr(assessment, "signals", []) if not isinstance(assessment, dict) else assessment.get("signals", [])
        risk_summary = [s.get("description") if isinstance(s, dict) else getattr(s, "description", str(s)) for s in signals_list[:6]]

        # ── STEP 4: LLM-Grounded Reasoning Narrative ───────────────────────────
        reasoning_summary = ""
        llm_provider: Optional[str] = None
        llm_model: Optional[str] = None

        try:
            claim_info = state.claim_data or {}
            cust_info = state.customer_data or {}
            curr_code = claim_info.get("currency", "INR") or "INR"

            system_prompt = (
                "You are an insurance claim analysis assistant. "
                "Your role is to synthesize evidence into a neutral, factual reasoning summary. "
                "Do NOT make a final claim decision. Do NOT state 'the claim is fraudulent'. "
                "Do NOT fabricate information not present in the evidence. "
                "Write in professional, clear language. Maximum 3 concise paragraphs."
            )

            user_prompt = f"""Synthesize the following evidence into a concise reasoning summary for an insurance claim analysis.

CLAIM CONTEXT:
- Claim ID: {state.claim_id}
- Category: {claim_info.get('category', 'Unknown')}
- Claimed Amount: {curr_code} {claim_info.get('claim_amount', 0):,.2f}
- Incident Date: {claim_info.get('incident_date', 'Unknown')}

FRAUD RISK ASSESSMENT:
{_build_fraud_summary(assessment)}

NORMALIZED EVIDENCE:
{_build_evidence_summary(evidence_items)}

AI RECOMMENDATION TYPE: {RECOMMENDATION_LABELS.get(recommendation_type, recommendation_type)}
{f'OVERRIDE REASON: {override_reason}' if override_reason else ''}

TASK: Write a 2–3 paragraph neutral reasoning summary explaining:
1. Key findings from the evidence and agent analysis
2. Risk factors and supporting factors identified
3. Why this recommendation type was produced

CRITICAL RULES:
- Do not state "the claim is fraudulent" or make definitive determinations
- Do not fabricate amounts, dates, or names not in the evidence above
- Reference only evidence actually provided above
- End with: "This is an AI-assisted advisory analysis requiring human officer review."
"""
            reasoning_summary = await generate_text(user_prompt, system_prompt=system_prompt, temperature=0.2)
            llm_provider = (settings.LLM_PROVIDER or "unknown").lower()
            llm_model = getattr(settings, "LLM_MODEL", None) or "default"

        except Exception as llm_err:
            logger.warning(f"RecommendationAgent: LLM reasoning generation failed: {str(llm_err)}")
            # Fallback to deterministic summary
            reasoning_summary = (
                f"AI reasoning narrative generation failed ({str(llm_err)[:80]}). "
                f"Recommendation is based on deterministic rule evaluation only. "
                f"Risk level: {assessment.risk_level.upper()}. "
                f"Signals triggered: {assessment.signal_count}. "
                f"{'Override applied: ' + (override_reason or '') if override_reason else ''} "
                "This analysis requires human officer review."
            )

        duration = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"RecommendationAgent: Completed in {duration}ms. "
            f"recommendation={recommendation_type}, confidence_basis={confidence_basis}"
        )

        return RecommendationResult(
            recommendation=recommendation_type,
            recommendation_label=RECOMMENDATION_LABELS.get(recommendation_type, recommendation_type),
            final_decision_made=False,
            requires_human_review=True,
            reasoning_summary=reasoning_summary,
            policy_references=policy_references,
            risk_summary=risk_summary,
            missing_information=missing_information,
            required_next_actions=required_next_actions,
            override_reason=override_reason,
            confidence_basis=confidence_basis,
            llm_provider=llm_provider,
            llm_model=llm_model,
            prompt_version=PROMPT_VERSION
        )
