from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import claim_service
from app.agents.state import ClaimHistoryResult, HistoricalClaimSummary
from app.core.logging import logger

class ClaimHistoryAgent:
    """Agent responsible for retrieving and analyzing customer claim history directly from PostgreSQL.
    Computes factual historical metrics without misinterpreting prior legitimate claims as fraudulent.
    """

    @staticmethod
    async def analyze(db: AsyncSession, customer_id: Optional[str], current_claim_id: Optional[str] = None) -> ClaimHistoryResult:
        logger.info(f"ClaimHistoryAgent starting analysis for customer {customer_id}...")
        if not customer_id:
            return ClaimHistoryResult(
                total_previous_claims=0,
                previous_claim_types=[],
                total_previous_claim_amount=0.0,
                approved_claims_count=0,
                rejected_claims_count=0,
                claims=[]
            )

        try:
            # Query all claims associated with customer_id from PostgreSQL
            all_cust_claims = await claim_service.list_claims(db, customer_id=customer_id, limit=200)
            
            # Exclude current claim being analyzed
            prior_claims = [c for c in all_cust_claims if str(c.id) != str(current_claim_id)]

            claim_summaries: List[HistoricalClaimSummary] = []
            claim_types_set = set()
            total_amount = 0.0
            approved_count = 0
            rejected_count = 0

            for c in prior_claims:
                claim_types_set.add(c.category)
                total_amount += (c.claim_amount or 0.0)
                
                status_str = str(c.status)
                if status_str.lower() in ["approved", "settled", "paid"]:
                    approved_count += 1
                elif status_str.lower() in ["rejected", "denied"]:
                    rejected_count += 1

                claim_summaries.append(HistoricalClaimSummary(
                    claim_id=str(c.id),
                    claim_number=str(c.claim_number),
                    category=str(c.category),
                    incident_date=str(c.incident_date or ""),
                    claim_amount=float(c.claim_amount or 0.0),
                    status=status_str
                ))

            logger.info(
                f"ClaimHistoryAgent completed for customer {customer_id}: "
                f"total_prior={len(claim_summaries)}, total_amount=${total_amount:,.2f}"
            )

            return ClaimHistoryResult(
                total_previous_claims=len(claim_summaries),
                previous_claim_types=sorted(list(claim_types_set)),
                total_previous_claim_amount=round(total_amount, 2),
                approved_claims_count=approved_count,
                rejected_claims_count=rejected_count,
                claims=claim_summaries
            )

        except Exception as e:
            logger.error(f"Error in ClaimHistoryAgent for customer {customer_id}: {str(e)}")
            return ClaimHistoryResult(
                total_previous_claims=0,
                previous_claim_types=[],
                total_previous_claim_amount=0.0,
                approved_claims_count=0,
                rejected_claims_count=0,
                claims=[]
            )
