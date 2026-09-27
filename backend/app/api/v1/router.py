from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    customers,
    policies,
    claims,
    documents,
    audit_logs,
    dashboard,
    memory,
    knowledge,
    fraud
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(claims.router, prefix="/claims", tags=["Claims"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(memory.router, prefix="/memory", tags=["Memory"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base & RAG"])
api_router.include_router(fraud.router, prefix="/fraud", tags=["Phase 7: Fraud Detection & Recommendation"])

