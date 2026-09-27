from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class CustomerBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    name: str = Field(..., description="Customer full name")
    phone: str = Field(..., description="Contact phone number")
    email: str = Field(..., description="Email address")
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    address: str = Field(..., description="Residential address")
    national_id: str = Field(..., description="National identifier / SSN")
    member_since: str = Field(..., description="Member registration date")
    risk_score: float = Field(0.0, description="Customer risk score (0-100)")

class CustomerCreate(CustomerBase):
    id: Optional[str] = Field(None, description="Optional custom customer ID")

class CustomerUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    risk_score: Optional[float] = None

class CustomerRead(CustomerBase):
    id: str = Field(..., description="Unique Customer ID")
