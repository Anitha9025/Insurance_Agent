import pytest
from app.agents.state import (
    EvidenceItem,
    ClaimWorkflowState,
    IntakeAgentResult,
    CustomerVerificationResult,
    PolicyValidationResult,
    DocumentAnalysisResult,
    DocumentVisionAnalysis,
    ClaimHistoryResult,
    FraudRiskAssessmentResult,
    RecommendationResult
)
from app.agents.evidence_normalization_agent import EvidenceNormalizationAgent
from app.agents.fraud_detection_agent import FraudDetectionAgent, SIGNAL_RULE_VERSION
from app.agents.recommendation_agent import RecommendationAgent


def test_evidence_normalization_agent():
    # Construct a sample state with various agent outputs
    state = ClaimWorkflowState(
        claim_id="CLM-TEST-001",
        claim_data={"claim_amount": 50000.0, "category": "Auto"},
        customer_verification=CustomerVerificationResult(
            verified=False,
            customer_found=True,
            mismatches=["Name on document does not match account name"],
            risk_score=40.0
        ),
        policy_validation=PolicyValidationResult(
            policy_found=True,
            policy_active=False,
            coverage_available=False,
            premium_status="Lapsed",
            issues=["Policy expired before incident date", "Premium payment overdue"]
        ),
        document_analysis=DocumentAnalysisResult(
            documents_analyzed=1,
            vision_analysis=[
                DocumentVisionAnalysis(
                    document_id=10,
                    document_type="Repair Estimate",
                    extracted_text="Front bumper damage estimate $5,000",
                    flagged_issues=["Amount on estimate exceeds claimed amount"],
                    confidence_score=0.88,
                    is_authentic=True
                )
            ],
            has_flagged_documents=True,
            evidence=["Document 10 has flagged issues"]
        ),
        claim_history=ClaimHistoryResult(
            total_previous_claims=6,
            rejected_claims_count=3,
            history_summary="High claim frequency with multiple rejections"
        )
    )

    items = EvidenceNormalizationAgent.normalize(state)
    assert len(items) > 0

    types = [item.evidence_type for item in items]
    assert "policy_period_violation" in types
    assert "premium_lapsed" in types
    assert "customer_mismatch" in types
    assert "claim_history_pattern" in types


def test_fraud_detection_agent_no_evidence():
    result = FraudDetectionAgent.assess([])
    assert result.risk_level == "unknown"
    assert result.rule_based_score == 0.0
    assert result.signal_count == 0
    assert result.requires_human_review is True
    assert len(result.missing_information) > 0


def test_fraud_detection_agent_high_risk():
    evidence_items = [
        EvidenceItem(
            evidence_id="ev-001",
            source_agent="PolicyValidationAgent",
            category="observed",
            evidence_type="policy_period_violation",
            field_name="policy_active",
            observed_value="False",
            expected_value="True",
            description="Policy expired prior to incident date",
            severity="high"
        ),
        EvidenceItem(
            evidence_id="ev-002",
            source_agent="PolicyValidationAgent",
            category="observed",
            evidence_type="premium_lapsed",
            field_name="premium_status",
            observed_value="Lapsed",
            expected_value="Paid",
            description="Policy premium is in Lapsed status",
            severity="high"
        ),
        EvidenceItem(
            evidence_id="ev-003",
            source_agent="CustomerVerificationAgent",
            category="observed",
            evidence_type="customer_mismatch",
            field_name="name",
            observed_value="John Doe",
            expected_value="Jane Doe",
            description="Customer identity mismatch on document",
            severity="medium"
        )
    ]

    result = FraudDetectionAgent.assess(evidence_items)
    assert result.risk_level == "high"
    assert result.rule_based_score >= 45.0
    assert result.signal_count == 3
    assert result.requires_human_review is True
    assert len(result.signals) == 3


@pytest.mark.asyncio
async def test_recommendation_agent_deterministic_override():
    state = ClaimWorkflowState(
        claim_id="CLM-TEST-002",
        claim_data={"claim_amount": 1000.0, "category": "Auto"},
        policy_validation=PolicyValidationResult(
            policy_found=True,
            policy_active=False,
            coverage_available=False,
            premium_status="Lapsed"
        ),
        customer_verification=CustomerVerificationResult(
            verified=True,
            customer_found=True
        )
    )

    assessment = FraudRiskAssessmentResult(
        risk_level="high",
        rule_based_score=60.0,
        score_rule_version=SIGNAL_RULE_VERSION,
        signal_count=2,
        signals=[],
        supporting_evidence=["Policy inactive"],
        contradictory_evidence=[],
        missing_information=[],
        uncertainties=[],
        requires_human_review=True
    )

    rec = await RecommendationAgent.recommend(state, [], assessment)
    assert rec.recommendation == "reject_recommended"
    assert rec.confidence_basis == "override"
    assert rec.final_decision_made is False
    assert rec.requires_human_review is True
    assert "Policy was not active" in rec.override_reason


@pytest.mark.asyncio
async def test_recommendation_agent_approval():
    state = ClaimWorkflowState(
        claim_id="CLM-TEST-003",
        claim_data={"claim_amount": 1200.0, "category": "Auto"},
        policy_validation=PolicyValidationResult(
            policy_found=True,
            policy_active=True,
            coverage_available=True,
            premium_status="Paid"
        ),
        customer_verification=CustomerVerificationResult(
            verified=True,
            customer_found=True
        )
    )

    assessment = FraudRiskAssessmentResult(
        risk_level="low",
        rule_based_score=0.0,
        score_rule_version=SIGNAL_RULE_VERSION,
        signal_count=0,
        signals=[],
        supporting_evidence=[],
        contradictory_evidence=[],
        missing_information=[],
        uncertainties=[],
        requires_human_review=True
    )

    items = [
        EvidenceItem(
            evidence_id="ev-101",
            source_agent="CustomerVerificationAgent",
            category="observed",
            evidence_type="customer_verified",
            description="Customer identity verified successfully",
            severity="info"
        )
    ]

    rec = await RecommendationAgent.recommend(state, items, assessment)
    assert rec.recommendation == "approve_recommended"
    assert rec.final_decision_made is False
    assert rec.requires_human_review is True
    assert rec.recommendation_label == "Approve Recommended"
