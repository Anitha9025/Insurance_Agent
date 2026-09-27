from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import customer_service
from app.core.logging import logger

router = APIRouter()

@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Customer",
    description="Registers a new customer / policyholder record."
)
async def create_customer_endpoint(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    existing = await customer_service.get_customer_by_national_id(db, payload.national_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with National ID '{payload.national_id}' already exists."
        )
    
    return await customer_service.create_customer(db, payload)

@router.get(
    "",
    response_model=List[CustomerRead],
    summary="List Customers",
    description="Retrieves list of customers with pagination support."
)
async def list_customers_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    return await customer_service.list_customers(db, skip=skip, limit=limit)

@router.get(
    "/{id}",
    response_model=CustomerRead,
    summary="Get Customer",
    description="Fetches a customer record by ID or National ID."
)
async def get_customer_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    customer = await customer_service.get_customer_by_id(db, id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{id}' not found."
        )
    return customer

@router.put(
    "/{id}",
    response_model=CustomerRead,
    summary="Update Customer",
    description="Updates existing customer details."
)
async def update_customer_endpoint(
    id: str,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    updated = await customer_service.update_customer(db, id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{id}' not found."
        )
    return updated
