from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class AIAgentStepBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    agent_name: str = Field(..., description="Name of the AI agent")
    status: str = Field("Pending", description="Step status ('Pending', 'Running', 'Completed', 'Warning', 'Failed')")
    timestamp: str = Field(..., description="Timestamp of execution")
    duration_ms: int = Field(0, description="Duration in milliseconds")
    output_summary: str = Field(..., description="Summary output of agent task")
    details: Optional[Dict[str, Any]] = Field(None, description="Structured agent metadata")

class AIAgentStepCreate(AIAgentStepBase):
    claim_id: str = Field(..., description="Claim ID")

class AIAgentStepRead(AIAgentStepBase):
    id: str = Field(..., description="Step ID")
    claim_id: str = Field(..., description="Claim ID")
