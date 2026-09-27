from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from app.schemas.customer import CustomerRead, CustomerCreate
from app.schemas.policy import PolicyRead, PolicyCreate
from app.schemas.document import ClaimDocumentRead
from app.schemas.agent_step import AIAgentStepRead
from app.schemas.recommendation import AIRecommendationRead

class HumanDecisionSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    action: str = Field(..., description="Action ('Approve', 'Reject', 'Request Additional Documents')")
    decided_by: str = Field(..., description="Officer name")
    decided_at: str = Field(..., description="Decision timestamp")
    reason: str = Field(..., description="Officer rationale statement")

class ClaimBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    title: str = Field(..., description="Claim title summary")
    description: str = Field(..., description="Detailed incident narrative")
    category: str = Field(..., description="Insurance Category ('Vehicle', 'Health', 'Home', 'Travel', 'Business')")
    priority: str = Field("Medium", description="Priority level ('Low', 'Medium', 'High', 'Emergency')")
    is_emergency: bool = Field(False, description="Emergency flag")
    status: str = Field("Submitted", description="Claim Status ('Draft', 'Submitted', 'Processing', 'Under Review', 'Approved', 'Rejected', 'Requires Documents')")
    incident_date: str = Field(..., description="Incident date (YYYY-MM-DD)")
    incident_time: str = Field(..., description="Incident time (HH:MM)")
    location: str = Field(..., description="Incident location address")
    claim_amount: float = Field(..., description="Claimed payout amount")
    approved_amount: Optional[float] = Field(None, description="Approved payout amount")
    currency: str = Field("INR", description="Currency code ('INR', 'USD', 'EUR', 'GBP')")
    assigned_officer: str = Field("Officer Sarah Jenkins", description="Assigned officer name")

    officer_notes: Optional[str] = Field(None, description="Officer notes")

class ClaimCreate(ClaimBase):
    claim_number: Optional[str] = Field(None, description="Optional custom claim number (auto-generated if empty)")
    customer_id: Optional[str] = Field(None, description="Existing Customer ID")
    customer: Optional[CustomerCreate] = Field(None, description="Inline Customer creation payload if new customer")
    policy_number: Optional[str] = Field(None, description="Existing Policy Number")
    policy: Optional[PolicyCreate] = Field(None, description="Inline Policy creation payload if new policy")

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Any

class ClaimUpdateDecision(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    action: str = Field(..., description="Officer Action ('Approve', 'Reject', 'Request Additional Documents')")
    reason: str = Field(..., description="Officer rationale statement")
    decided_by: Optional[str] = Field("Officer Sarah Jenkins", description="Deciding officer name")

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "human_decision_action" in data and "action" not in data:
                data["action"] = data["human_decision_action"]
            if "officer_notes" in data and "reason" not in data:
                data["reason"] = data["officer_notes"]
            if "human_decision_by" in data and "decided_by" not in data and "decidedBy" not in data:
                data["decided_by"] = data["human_decision_by"]
        return data

class ClaimRead(ClaimBase):
    id: str = Field(..., description="Unique Claim ID")
    claim_number: str = Field(..., description="Unique Claim Number (e.g. CLM-2026-8841)")
    created_at: Union[datetime, str] = Field(..., description="Record creation timestamp")
    updated_at: Union[datetime, str] = Field(..., description="Record update timestamp")
    customer: CustomerRead = Field(..., description="Policyholder Customer details")
    policy: PolicyRead = Field(..., description="Associated Policy details")
    documents: List[ClaimDocumentRead] = Field(default_factory=list, description="Claim documents")
    agent_steps: List[AIAgentStepRead] = Field(default_factory=list, description="Execution progress steps")
    ai_recommendation: Optional[AIRecommendationRead] = Field(None, description="AI recommendation synthesis")
    human_decision: Optional[HumanDecisionSchema] = Field(None, description="Human officer decision details")
