"""
Fraud Detection Agent — Phase 7
Applies deterministic, configurable signal rules against normalized EvidenceItem list.
LLM is used only for generating neutral narrative text, not for scoring.
No fraud patterns are hardcoded. Signal logic is pure Python rule evaluation.
"""
import time
from typing import List, Optional
from app.agents.state import (
    EvidenceItem,
    FraudRiskSignal,
    FraudRiskAssessmentResult,
)
from app.core.logging import logger

# ── Signal Rule Configuration ─────────────────────────────────────────────────
# Each rule maps an evidence_type to (signal_type, severity, score_contribution)
# score_contribution is the amount this signal adds to the composite risk score (0–100)
SIGNAL_RULE_VERSION = "v1.0"

SIGNAL_RULES = [
    # (evidence_type_match_keyword, signal_type, severity, score_contribution)
    ("policy_period_violation",       "policy_period_violation",       "high",   30.0),
    ("premium_lapsed",                "premium_lapsed",                "high",   30.0),
    ("policy_ownership_mismatch",     "policy_ownership_mismatch",     "high",   35.0),
    ("customer_name_mismatch",        "customer_name_mismatch",        "high",   25.0),
    ("customer_name_spelling_variation", "customer_name_spelling_variation", "medium", 12.0),
    ("policy_number_mismatch",        "policy_number_mismatch",        "high",   30.0),
    ("vehicle_registration_mismatch", "vehicle_registration_mismatch", "high",   25.0),
    ("vehicle_registration_spelling_variation", "vehicle_registration_spelling_variation", "medium", 10.0),
    ("chassis_number_mismatch",       "chassis_number_mismatch",       "high",   25.0),
    ("chassis_number_spelling_variation", "chassis_number_spelling_variation", "medium", 10.0),
    ("email_mismatch",                "email_mismatch",                "medium", 15.0),
    ("phone_mismatch",                "phone_mismatch",                "medium", 15.0),
    ("incident_date_mismatch",        "incident_date_mismatch",        "medium", 15.0),
    ("coverage_exceeded",             "coverage_limit_exceeded",       "high",   20.0),
    ("category_mismatch",             "category_mismatch",             "high",   25.0),
    ("customer_mismatch",             "customer_identity_mismatch",    "high",   20.0),
    ("document_mismatch",             "document_inconsistency",        "medium", 12.0),
    ("policy_document_unavailable",   "policy_document_unavailable",   "medium", 15.0),
    ("vision_conflict",               "visual_evidence_conflict",      "medium", 10.0),
    ("missing_document",              "missing_required_document",     "medium",  8.0),
    ("claim_history_pattern",         "high_claim_frequency",          "low",     5.0),
    ("rag_clause_unavailable",        "policy_clause_unverifiable",    "low",     3.0),
]

# CONTRADICTORY (positive) evidence types that reduce ambiguity
POSITIVE_EVIDENCE_TYPES = {
    "customer_verified",
    "document_verified",
    "policy_active",
    "coverage_confirmed",
    "claim_history_normal",
    "general_observation",
}


def _compute_risk_level(score: float, signal_count: int) -> str:
    """Derives risk level from composite score.
    0–19 Low risk, 20–49 Moderate/Medium risk, 50–74 High risk, 75–100 Critical risk.
    """
    if signal_count == 0:
        return "low"
    if score >= 75.0:
        return "critical"
    elif score >= 50.0:
        return "high"
    elif score >= 20.0:
        return "medium"
    elif score > 0:
        return "low"
    return "unknown"


class FraudDetectionAgent:
    """Phase 7 Fraud Detection Agent.
    Applies rule-based signal detection on normalized evidence. Never fabricates scores.
    LLM augments narrative explanation only (not invoked in this synchronous class).
    """

    @staticmethod
    def assess(evidence_items: List[EvidenceItem]) -> FraudRiskAssessmentResult:
        start_time = time.time()
        logger.info(f"FraudDetectionAgent: Assessing {len(evidence_items)} evidence items...")

        if not evidence_items:
            return FraudRiskAssessmentResult(
                risk_level="unknown",
                rule_based_score=0.0,
                score_rule_version=SIGNAL_RULE_VERSION,
                signal_count=0,
                signals=[],
                supporting_evidence=[],
                contradictory_evidence=[],
                missing_information=["No evidence items were available for assessment."],
                uncertainties=["Assessment cannot be completed without evidence."],
                requires_human_review=True
            )

        signals: List[FraudRiskSignal] = []
        supporting_evidence: List[str] = []
        contradictory_evidence: List[str] = []
        missing_information: List[str] = []
        uncertainties: List[str] = []

        # Deduplicate by signal_type: only one signal per type, but accumulate evidence_ids
        signal_map: dict = {}  # signal_type -> {evidence_ids, severity, score, description_parts}

        for item in evidence_items:
            if isinstance(item, dict):
                ev_type = item.get("evidence_type") or item.get("evidenceType") or ""
                severity = item.get("severity", "info")
                category = item.get("category", "observed")
                description = item.get("description", "")
                evidence_id = item.get("evidence_id") or item.get("evidenceId") or "ev-000"
                field_name = item.get("field_name") or item.get("fieldName")
            else:
                ev_type = getattr(item, "evidence_type", "")
                severity = getattr(item, "severity", "info")
                category = getattr(item, "category", "observed")
                description = getattr(item, "description", "")
                evidence_id = getattr(item, "evidence_id", "ev-000")
                field_name = getattr(item, "field_name", None)

            # --- Check against signal rules ---
            matched_rule = None
            for (keyword, sig_type, sig_sev, sig_score) in SIGNAL_RULES:
                if ev_type == keyword or (severity in ("high", "medium") and keyword in ev_type):
                    matched_rule = (sig_type, sig_sev, sig_score)
                    break

            if matched_rule and category in ("observed", "inferred"):
                sig_type, sig_sev, sig_score = matched_rule
                if sig_type not in signal_map:
                    signal_map[sig_type] = {
                        "evidence_ids": [],
                        "severity": sig_sev,
                        "score": sig_score,
                        "descriptions": []
                    }
                signal_map[sig_type]["evidence_ids"].append(evidence_id)
                signal_map[sig_type]["descriptions"].append(description)
                supporting_evidence.append(f"[{evidence_id}] {description}")
            elif ev_type in POSITIVE_EVIDENCE_TYPES:
                contradictory_evidence.append(f"[{evidence_id}] {description}")
            elif category == "unknown":
                uncertainties.append(f"[{evidence_id}] {description}")

        # Build FraudRiskSignal objects from signal_map
        sig_counter = 0
        composite_score = 0.0
        for sig_type, sig_data in signal_map.items():
            sig_counter += 1
            composite_score += sig_data["score"]
            # Cap score at 100
            composite_score = min(composite_score, 100.0)

            description = sig_data["descriptions"][0] if sig_data["descriptions"] else f"Signal type '{sig_type}' triggered."
            if len(sig_data["descriptions"]) > 1:
                description = f"{description} ({len(sig_data['descriptions']) - 1} additional related item(s) detected.)"

            signals.append(FraudRiskSignal(
                signal_id=f"sig-{sig_counter:03d}",
                signal_type=sig_type,
                evidence_ids=sig_data["evidence_ids"],
                severity=sig_data["severity"],
                description=description,
                rule_version=SIGNAL_RULE_VERSION,
                score_contribution=sig_data["score"]
            ))

        # Collect missing information from evidence
        for item in evidence_items:
            ev_t = item.get("evidence_type") if isinstance(item, dict) else getattr(item, "evidence_type", "")
            f_name = item.get("field_name") if isinstance(item, dict) else getattr(item, "field_name", None)
            if ev_t == "missing_document" and f_name:
                missing_information.append(f"Missing field or document: '{f_name}'.")

        risk_level = _compute_risk_level(composite_score, len(signals))
        duration = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"FraudDetectionAgent: Completed in {duration}ms. "
            f"risk_level={risk_level}, score={composite_score:.1f}, signals={len(signals)}"
        )

        return FraudRiskAssessmentResult(
            risk_level=risk_level,
            rule_based_score=round(composite_score, 2),
            score_rule_version=SIGNAL_RULE_VERSION,
            signal_count=len(signals),
            signals=signals,
            supporting_evidence=supporting_evidence,
            contradictory_evidence=contradictory_evidence,
            missing_information=missing_information,
            uncertainties=uncertainties,
            requires_human_review=True
        )
