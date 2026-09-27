from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class AgentExecutionMeta(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    agent_name: str = Field(..., description="Name of the executed agent")
    status: str = Field("completed", description="'completed', 'failed', or 'skipped'")
    timestamp: str = Field(..., description="ISO timestamp of execution")
    duration_ms: float = Field(0.0, description="Execution duration in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during agent execution")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during agent execution")
    evidence: List[str] = Field(default_factory=list, description="Factual evidence collected by agent")

class IntakeAgentResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    claim_id: str = Field(..., description="Claim ID evaluated")
    claim_data_available: bool = Field(True, description="Whether claim record exists in database")
    claim_type: Optional[str] = Field(None, description="Category of the claim (e.g. Vehicle, Health, Home)")
    claim_amount: Optional[float] = Field(None, description="Claim amount submitted")
    incident_date: Optional[str] = Field(None, description="Incident date")
    description: Optional[str] = Field(None, description="Detailed incident description")
    documents_submitted_count: int = Field(0, description="Count of attached documents")
    missing_information: List[str] = Field(default_factory=list, description="Missing required claim fields")
    warnings: List[str] = Field(default_factory=list, description="Intake warnings")

class CustomerFieldMismatch(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    field: str = Field(..., description="Field name with mismatch")
    claim_value: Optional[str] = Field(None, description="Value on claim registration")
    database_value: Optional[str] = Field(None, description="Value in customer database record")

class CustomerVerificationResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    customer_found: bool = Field(True, description="Whether customer record exists in database")
    verified: bool = Field(False, description="True if key customer details match database record")
    matched_fields: List[str] = Field(default_factory=list, description="List of verified matching fields")
    mismatches: List[CustomerFieldMismatch] = Field(default_factory=list, description="List of mismatched fields")
    missing_fields: List[str] = Field(default_factory=list, description="List of unprovided customer fields")
    risk_score: Optional[float] = Field(None, description="Customer risk score from profile")
    member_since: Optional[str] = Field(None, description="Customer membership start date")

class DocumentItemAnalysis(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original file name")
    document_type: str = Field(..., description="Classified document category")
    ocr_status: str = Field("Pending", description="OCR processing status")
    verification_status: str = Field("Pending", description="Verification status ('Verified', 'Flagged')")
    extracted_fields_count: int = Field(0, description="Count of extracted OCR fields")
    vision_analysis: Optional[Dict[str, Any]] = Field(None, description="Phase 4 dynamic cloud vision analysis result")

class DocumentAnalysisResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    documents_analyzed: int = Field(0, description="Number of documents analyzed")
    documents: List[DocumentItemAnalysis] = Field(default_factory=list, description="Per-document analysis details")
    evidence: List[str] = Field(default_factory=list, description="Aggregated factual visual and textual evidence")
    uncertainties: List[str] = Field(default_factory=list, description="Uncertainties or unverified document items")
    has_flagged_documents: bool = Field(False, description="True if any document is flagged for human review")

class PolicyCheckItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    check: str = Field(..., description="Check description e.g. 'policy_period', 'coverage_limit'")
    status: str = Field(..., description="'passed', 'failed', or 'warning'")
    evidence: str = Field(..., description="Factual evidence supporting check outcome")

class PolicyValidationResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    policy_found: bool = Field(False, description="Whether policy record exists in database")
    policy_active: bool = Field(False, description="True if incident date falls within policy period")
    coverage_available: bool = Field(False, description="True if claim amount is within coverage limit")
    policy_number: Optional[str] = Field(None, description="Policy number")
    category: Optional[str] = Field(None, description="Policy category")
    premium_status: Optional[str] = Field(None, description="Premium payment status")
    coverage_limit: Optional[float] = Field(None, description="Policy coverage limit")
    deductible: Optional[float] = Field(None, description="Standard deductible amount")
    checks: List[PolicyCheckItem] = Field(default_factory=list, description="Individual policy validation checks")
    issues: List[str] = Field(default_factory=list, description="Policy validation issues or violations")
    policy_clause_validation_status: str = Field(
        "policy_clause_validation_pending",
        description="Placeholder indicating detailed RAG policy clause validation will be executed in later phase"
    )

class HistoricalClaimSummary(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    claim_id: str = Field(..., description="Historical claim ID")
    claim_number: str = Field(..., description="Claim number")
    category: str = Field(..., description="Claim category")
    incident_date: str = Field(..., description="Incident date")
    claim_amount: float = Field(0.0, description="Submitted claim amount")
    status: str = Field(..., description="Claim status e.g. 'Approved', 'Rejected'")

class ClaimHistoryResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_previous_claims: int = Field(0, description="Count of prior claims for customer")
    previous_claim_types: List[str] = Field(default_factory=list, description="Unique categories of previous claims")
    total_previous_claim_amount: float = Field(0.0, description="Sum of previous submitted claim amounts")
    approved_claims_count: int = Field(0, description="Number of previously approved claims")
    rejected_claims_count: int = Field(0, description="Number of previously rejected claims")
    claims: List[HistoricalClaimSummary] = Field(default_factory=list, description="List of historical claim records")

class ClaimWorkflowState(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    claim_id: str = Field(..., description="Target claim ID being evaluated")
    customer_id: Optional[str] = Field(None, description="Associated customer ID")
    policy_number: Optional[str] = Field(None, description="Associated policy number")

    claim_data: Optional[Dict[str, Any]] = Field(None, description="Raw claim database record snapshot")
    customer_data: Optional[Dict[str, Any]] = Field(None, description="Raw customer database record snapshot")
    policy_data: Optional[Dict[str, Any]] = Field(None, description="Raw policy database record snapshot")
    documents_data: List[Dict[str, Any]] = Field(default_factory=list, description="Raw document records snapshot")

    intake_analysis: Optional[IntakeAgentResult] = Field(None, description="Result from Claim Intake Agent")
    customer_verification: Optional[CustomerVerificationResult] = Field(None, description="Result from Customer Verification Agent")
    document_analysis: Optional[DocumentAnalysisResult] = Field(None, description="Result from Document Analysis Agent")
    policy_validation: Optional[PolicyValidationResult] = Field(None, description="Result from Policy Validation Agent")
    claim_history: Optional[ClaimHistoryResult] = Field(None, description="Result from Claim History Agent")
    rag_analysis: Optional[Dict[str, Any]] = Field(None, description="Result from RAG Knowledge Agent")
    retrieved_memories: Optional[Dict[str, Any]] = Field(None, description="Result from Memory Agent")
    db_tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Log of controlled database tool executions")

    # --- Phase 7: Dynamic Fraud Detection + Recommendation ---
    normalized_evidence: List["EvidenceItem"] = Field(default_factory=list, description="Phase 7: Normalized evidence items from all prior agents")
    fraud_assessment: Optional["FraudRiskAssessmentResult"] = Field(None, description="Phase 7: Evidence-based fraud risk assessment")
    recommendation: Optional["RecommendationResult"] = Field(None, description="Phase 7: AI-assisted claim recommendation (not a final decision)")

    agent_meta: Dict[str, AgentExecutionMeta] = Field(default_factory=dict, description="Metadata per executed agent")
    validation_errors: List[str] = Field(default_factory=list, description="Validation issues accumulated")
    warnings: List[str] = Field(default_factory=list, description="System-wide workflow warnings")
    errors: List[str] = Field(default_factory=list, description="Agent or database execution errors")
    completed_agents: List[str] = Field(default_factory=list, description="List of agent names successfully completed")
    workflow_status: str = Field("pending", description="'pending', 'in_progress', 'completed', or 'failed'")


# ── Phase 7: Shared Evidence Model ────────────────────────────────────────────

class EvidenceItem(BaseModel):
    """A single normalized, source-attributed evidence item produced by the Evidence Normalization Agent.
    Language must be neutral and factual. No fraud labels applied at this stage.
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evidence_id: str = Field(..., description="Unique identifier for this evidence item (e.g. 'ev-001')")
    source_agent: str = Field(..., description="Name of the agent that produced this evidence")
    evidence_type: str = Field(
        ...,
        description=(
            "One of: customer_mismatch, policy_period_violation, coverage_exceeded, "
            "document_mismatch, claim_history_pattern, missing_document, "
            "rag_clause_unavailable, vision_conflict, category_mismatch, premium_lapsed, "
            "coverage_confirmed, customer_verified, document_verified, policy_active, "
            "claim_history_normal, general_observation"
        )
    )
    category: Literal["observed", "inferred", "unknown"] = Field(
        ...,
        description="Certainty category: 'observed' (directly from data), 'inferred' (derived), 'unknown' (cannot determine)"
    )
    description: str = Field(..., description="Neutral, factual description of the evidence")
    source_document_id: Optional[str] = Field(None, description="Document ID if evidence originates from a specific document")
    field_name: Optional[str] = Field(None, description="Specific data field that produced the evidence")
    observed_value: Optional[str] = Field(None, description="Actual value observed in source data")
    expected_value: Optional[str] = Field(None, description="Expected or registered value for comparison")
    severity: Literal["info", "low", "medium", "high"] = Field("info", description="Severity level of this evidence item")


class FraudRiskSignal(BaseModel):
    """A single fraud risk indicator derived from an evidence item."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    signal_id: str = Field(..., description="Unique signal identifier (e.g. 'sig-001')")
    signal_type: str = Field(..., description="Rule type that triggered this signal")
    evidence_ids: List[str] = Field(default_factory=list, description="List of evidence item IDs that triggered this signal")
    severity: Literal["low", "medium", "high"] = Field(..., description="Signal severity level")
    description: str = Field(..., description="Neutral description of what this signal indicates")
    rule_version: str = Field("v1.0", description="Version of the signal rule that was applied")
    score_contribution: float = Field(0.0, description="Score contribution of this signal to overall risk indicator (0–100)")


class FraudRiskAssessmentResult(BaseModel):
    """Phase 7 evidence-based fraud risk assessment result.
    Does not make a final fraud determination. Always requires human review.
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    risk_level: Literal["low", "medium", "high", "critical", "unknown"] = Field(
        ...,
        description="Overall risk indicator level derived from rule-based signal analysis"
    )
    rule_based_score: float = Field(
        ...,
        description="Composite risk indicator score (0–100). Higher = more signals triggered. Not a definitive fraud probability."
    )
    score_rule_version: str = Field("v1.0", description="Version string for the scoring rule set")
    signal_count: int = Field(0, description="Number of risk signals triggered")
    signals: List[FraudRiskSignal] = Field(default_factory=list, description="All triggered risk signals")
    supporting_evidence: List[str] = Field(default_factory=list, description="Evidence items that support elevated risk interpretation")
    contradictory_evidence: List[str] = Field(default_factory=list, description="Evidence items that contradict elevated risk interpretation")
    missing_information: List[str] = Field(default_factory=list, description="Information gaps that prevent full assessment")
    uncertainties: List[str] = Field(default_factory=list, description="Items the system could not classify with confidence")
    requires_human_review: bool = Field(True, description="Always True — AI assessment requires human validation")
    assessment_disclaimer: str = Field(
        "This is an AI-assisted risk assessment based on rule-derived signals. "
        "It does not constitute a fraud determination. Final decision authority rests with the human officer.",
        description="Mandatory disclaimer for all Phase 7 assessments"
    )
    llm_provider: Optional[str] = Field(None, description="LLM provider used for narrative explanation")
    llm_model: Optional[str] = Field(None, description="LLM model used for narrative explanation")


class RecommendationResult(BaseModel):
    """Phase 7 AI-assisted claim recommendation.
    Must never override human officer authority. Always advisory only.
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    recommendation: Literal[
        "approve_recommended",
        "reject_recommended",
        "request_more_information",
        "manual_review_required",
        "insufficient_evidence",
        "processing_failed"
    ] = Field(..., description="AI-assisted recommendation type. Not a final decision.")
    recommendation_label: str = Field(..., description="Human-readable label for recommendation type")
    final_decision_made: bool = Field(False, description="Always False — AI does not make final decisions")
    requires_human_review: bool = Field(True, description="Always True — officer must validate AI recommendation")
    reasoning_summary: str = Field(..., description="LLM-grounded narrative synthesizing all agent evidence")
    policy_references: List[str] = Field(default_factory=list, description="Relevant policy clauses and RAG knowledge citations")
    risk_summary: List[str] = Field(default_factory=list, description="Summary of key risk signals from fraud assessment")
    missing_information: List[str] = Field(default_factory=list, description="Information that would improve recommendation quality")
    required_next_actions: List[str] = Field(default_factory=list, description="Specific actions recommended for human officer review")
    override_reason: Optional[str] = Field(None, description="If deterministic override applied, the rule that was triggered")
    confidence_basis: str = Field("evidence", description="Basis for recommendation confidence: 'evidence', 'override', 'insufficient'")
    llm_provider: Optional[str] = Field(None, description="LLM provider used for reasoning")
    llm_model: Optional[str] = Field(None, description="LLM model used for reasoning")
    prompt_version: str = Field("v1.0", description="Prompt template version")
    officer_decision_disclaimer: str = Field(
        "This AI-generated recommendation is advisory only. The insurance officer retains full decision authority and is not bound by this output.",
        description="Mandatory officer advisory disclaimer"
    )


# Allow forward references in ClaimWorkflowState to resolve
ClaimWorkflowState.model_rebuild()

