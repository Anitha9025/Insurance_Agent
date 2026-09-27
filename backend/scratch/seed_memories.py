import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.claim import Claim
from app.models.memory import ClaimMemory
from app.services.memory_service import MemoryService

async def seed():
    async with AsyncSessionLocal() as db:
        claims_res = await db.execute(select(Claim))
        claims = claims_res.scalars().all()
        print(f"Found {len(claims)} active claims in database.")

        for c in claims:
            mem_res = await db.execute(select(ClaimMemory).where(ClaimMemory.claim_id == c.id))
            existing = mem_res.scalars().all()
            if not existing:
                print(f"Seeding memories for claim {c.claim_number} ({c.id})...")
                await MemoryService.add_memory(
                    db=db,
                    claim_id=c.id,
                    memory_type="officer_decision",
                    memory_key="policy_coverage_deductible_approval",
                    memory_value=f"Approved payout for claim {c.claim_number} ({c.title}) after deducting policy deductible ($500). Incident date: {c.incident_date}.",
                    confidence_score=0.98,
                    source_agent="Coordinator Agent"
                )
                await MemoryService.add_memory(
                    db=db,
                    claim_id=c.id,
                    memory_type="fraud_analysis",
                    memory_key="low_risk_verification",
                    memory_value=f"Verified low fraud risk score (14/100) for claim {c.claim_number}. Policy premiums fully paid and documentation validated.",
                    confidence_score=0.95,
                    source_agent="Fraud Agent"
                )
                await MemoryService.add_memory(
                    db=db,
                    claim_id=c.id,
                    memory_type="financial_valuation",
                    memory_key="payout_calculation",
                    memory_value=f"Financial Agent assessed total requested amount of ${c.claim_amount:,.2f} and calculated recommended payout after coverage limit adjustments.",
                    confidence_score=0.96,
                    source_agent="Financial Agent"
                )
        print("Memory seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
