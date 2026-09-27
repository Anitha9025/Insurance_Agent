from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class AIRecommendationBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    verdict: str = Field(..., description="Verdict ('Approve', 'Reject', 'Request Additional Documents')")
    confidence_score: float = Field(..., description="Confidence score (0 to 100)")
    fraud_risk_score: float = Field(..., description="Fraud risk score (0 to 100)")
    recommended_amount: float = Field(..., description="Recommended payout amount")
    reasoning_summary: str = Field(..., description="Synthesized reasoning explanation")
    key_findings: List[str] = Field(default_factory=list, description="List of key evidence findings")
    risk_flags: List[str] = Field(default_factory=list, description="List of identified risk flags")
    retrieved_memories: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved LangMem case memories")
    retrieved_knowledge: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved RAG knowledge documents")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Executed factual tool logs")

class AIRecommendationCreate(AIRecommendationBase):
    claim_id: str = Field(..., description="Target Claim ID")

class AIRecommendationRead(AIRecommendationBase):
    id: str = Field(..., description="Recommendation ID")
    claim_id: str = Field(..., description="Target Claim ID")
