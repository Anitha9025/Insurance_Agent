from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class PolicyBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    category: str = Field(..., description="Insurance Category ('Vehicle', 'Health', 'Home', 'Travel', 'Business')")
    start_date: str = Field(..., description="Policy active start date")
    end_date: str = Field(..., description="Policy active end date")
    premium_status: str = Field("Paid", description="Premium status ('Paid', 'Pending', 'Grace Period', 'Overdue')")
    coverage_limit: float = Field(..., description="Maximum policy coverage limit")
    deductible: float = Field(..., description="Policy deductible amount")
    active_claims_count: int = Field(0, description="Count of currently active claims")

class PolicyCreate(PolicyBase):
    policy_number: str = Field(..., description="Unique Policy Number (e.g. POL-AUTO-99824)")
    customer_id: Optional[str] = Field(None, description="Associated Customer ID")

class PolicyUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    premium_status: Optional[str] = None
    coverage_limit: Optional[float] = None
    deductible: Optional[float] = None
    active_claims_count: Optional[int] = None

class PolicyRead(PolicyBase):
    policy_number: str = Field(..., description="Unique Policy Number")
    customer_id: str = Field(..., description="Associated Customer ID")


class PolicyVerificationRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    policy_number: str = Field(..., description="Policy Number to retrieve and verify")
    incident_date: Optional[str] = Field(None, description="Optional incident date to check policy coverage period")


class PolicyVerificationResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str = Field(
        ...,
        description="Policy verification status ('policy_found', 'policy_not_found', 'policy_inactive', 'policy_expired', 'policy_document_unavailable', 'policy_verification_required')"
    )
    policy_number: str = Field(..., description="Policy Number verified")
    policy_exists: bool = Field(False, description="True if policy record exists in database")
    is_active: bool = Field(False, description="True if policy dates and premium status are currently active")
    is_expired: bool = Field(False, description="True if policy end date precedes incident/current date")
    category: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    premium_status: Optional[str] = Field(None)
    coverage_limit: Optional[float] = Field(None)
    deductible: Optional[float] = Field(None)
    currency: Optional[str] = Field("INR", description="Policy currency e.g. INR or USD")

    customer_id: Optional[str] = Field(None)
    customer_name: Optional[str] = Field(None)
    customer_email: Optional[str] = Field(None)
    customer_phone: Optional[str] = Field(None)
    specific_details: Optional[dict] = Field(default_factory=dict, description="Category specific details (vehicle/health details)")

    policy_document_available: bool = Field(False, description="True if customer-specific policy document is ingested in Knowledge Base")
    policy_document_id: Optional[str] = Field(None)
    policy_document_title: Optional[str] = Field(None)

    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

