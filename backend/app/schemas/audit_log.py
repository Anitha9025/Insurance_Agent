from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class AuditLogBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    timestamp: str = Field(..., description="Action timestamp ISO string")
    actor_type: str = Field(..., description="Actor type ('Officer' or 'AI Agent')")
    actor_name: str = Field(..., description="Name of the actor executing action")
    action: str = Field(..., description="Action summary description")
    details: str = Field(..., description="Detailed log narrative")
    memory_used: Optional[str] = Field(None, description="Referenced memory ID")
    knowledge_used: Optional[str] = Field(None, description="Referenced policy clause code")
    tools_called: Optional[List[str]] = Field(None, description="List of called database tools")
    ip_address: Optional[str] = Field(None, description="Client IP address")

class AuditLogCreate(AuditLogBase):
    claim_id: Optional[str] = Field(None, description="Target Claim ID")
    claim_number: Optional[str] = Field(None, description="Target Claim Number")

class AuditLogRead(AuditLogBase):
    id: str = Field(..., description="Audit Log ID")
    claim_id: Optional[str] = Field(None, description="Target Claim ID")
    claim_number: Optional[str] = Field(None, description="Target Claim Number")
