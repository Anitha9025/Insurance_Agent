from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class DatabaseHealth(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str = Field(..., description="Database connection status ('connected' or 'disconnected')")
    database_type: str = Field(..., description="Database dialect driver")
    error: Optional[str] = Field(None, description="Detailed error message if disconnected")

class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str = Field("ok", description="Backend service health status")
    version: str = Field(..., description="API Version")
    timestamp: str = Field(..., description="Current UTC timestamp ISO string")
    environment: str = Field(..., description="Application execution environment")
    database: DatabaseHealth = Field(..., description="Database health status")
    services: Dict[str, str] = Field(default_factory=dict, description="AI/External Services health metadata")
