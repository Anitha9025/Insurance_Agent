"""
Phase 7: Pydantic schemas for Fraud Assessment and Recommendation API responses.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class FraudRiskSignalSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    signal_id: str
    signal_type: str
    evidence_ids: List[str] = Field(default_factory=list)
    severity: str
    description: str
    rule_version: str
    score_contribution: float


class FraudAssessmentRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    claim_id: str
    risk_level: str = Field(..., description="low | medium | high | unknown")
    rule_based_score: float = Field(..., description="Composite rule-based risk indicator (0–100)")
    score_rule_version: str
    signal_count: int
    assessment_status: str
    signals_json: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence_json: List[str] = Field(default_factory=list)
    contradictory_evidence_json: List[str] = Field(default_factory=list)
    missing_information_json: List[str] = Field(default_factory=list)
    uncertainties_json: List[str] = Field(default_factory=list)
    normalized_evidence_json: List[Dict[str, Any]] = Field(default_factory=list)
    requires_human_review: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    assessment_disclaimer: Optional[str] = None


class RecommendationRecordRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    claim_id: str
    recommendation: str = Field(..., description="approve_recommended | reject_recommended | request_more_information | manual_review_required | insufficient_evidence | processing_failed")
    recommendation_label: str
    reasoning_summary: str
    policy_references_json: List[str] = Field(default_factory=list)
    risk_summary_json: List[str] = Field(default_factory=list)
    missing_information_json: List[str] = Field(default_factory=list)
    required_next_actions_json: List[str] = Field(default_factory=list)
    override_reason: Optional[str] = None
    confidence_basis: str
    requires_human_review: bool
    final_decision_made: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    prompt_version: str


class Phase7AnalysisResponse(BaseModel):
    """Combined Phase 7 response returned by the analyze endpoint."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    claim_id: str
    fraud_assessment: Optional[FraudAssessmentRead] = None
    recommendation: Optional[RecommendationRecordRead] = None
    normalized_evidence_count: int = 0
    workflow_status: str
    message: str
