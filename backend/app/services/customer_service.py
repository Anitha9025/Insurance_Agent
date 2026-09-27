from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.core.logging import logger

async def create_customer(db: AsyncSession, payload: CustomerCreate) -> Customer:
    """Creates a new customer record."""
    cust_kwargs = {
        "name": payload.name,
        "phone": payload.phone,
        "email": payload.email,
        "dob": payload.dob,
        "address": payload.address,
        "national_id": payload.national_id,
        "member_since": payload.member_since,
        "risk_score": payload.risk_score
    }
    if payload.id:
        cust_kwargs["id"] = payload.id

    customer = Customer(**cust_kwargs)
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    logger.info(f"Created customer {customer.name} ({customer.id})")
    return customer

async def get_customer_by_id(db: AsyncSession, customer_id: str) -> Optional[Customer]:
    """Fetches customer by unique ID or national ID."""
    stmt = select(Customer).where((Customer.id == customer_id) | (Customer.national_id == customer_id))
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def get_customer_by_national_id(db: AsyncSession, national_id: str) -> Optional[Customer]:
    """Fetches customer by national ID / SSN."""
    stmt = select(Customer).where(Customer.national_id == national_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_customers(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Customer]:
    """Lists customers with pagination."""
    stmt = select(Customer).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def update_customer(db: AsyncSession, customer_id: str, payload: CustomerUpdate) -> Optional[Customer]:
    """Updates an existing customer record."""
    customer = await get_customer_by_id(db, customer_id)
    if not customer:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.flush()
    await db.refresh(customer)
    logger.info(f"Updated customer {customer.id}")
    return customer
