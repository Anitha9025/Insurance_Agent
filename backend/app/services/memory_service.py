import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.memory import ClaimMemory
from app.models.claim import Claim
from app.core.cloud_embedding import generate_embedding
from app.core.logging import logger

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    dim = min(len(vec1), len(vec2))
    dot = sum(vec1[i] * vec2[i] for i in range(dim))
    norm1 = math.sqrt(sum(vec1[i] * vec1[i] for i in range(dim)))
    norm2 = math.sqrt(sum(vec2[i] * vec2[i] for i in range(dim)))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class MemoryService:
    @staticmethod
    async def add_memory(
        db: AsyncSession,
        claim_id: str,
        memory_type: str,
        memory_key: str,
        memory_value: str,
        confidence_score: float = 1.0,
        source_agent: str = "system"
    ) -> ClaimMemory:
        """
        Store a validated insight, decision rationale, or policy rule memory for a claim with vector embeddings.
        """
        text_to_embed = f"{memory_type} {memory_key}: {memory_value}"
        emb = await generate_embedding(text_to_embed)

        mem = ClaimMemory(
            claim_id=claim_id,
            memory_type=memory_type,
            memory_key=memory_key,
            memory_value=memory_value,
            embedding=emb,
            confidence_score=confidence_score,
            source_agent=source_agent
        )
        db.add(mem)
        await db.commit()
        await db.refresh(mem)
        logger.info(f"Added ClaimMemory ({mem.id}) for claim {claim_id} by {source_agent}.")
        return mem

    @staticmethod
    async def get_claim_memories(db: AsyncSession, claim_id: str) -> List[ClaimMemory]:
        """Retrieve all memory records stored for a specific claim."""
        stmt = select(ClaimMemory).where(ClaimMemory.claim_id == claim_id).order_by(ClaimMemory.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def search_memories(
        db: AsyncSession,
        query: str,
        category: Optional[str] = None,
        top_k: int = 10,
        exclude_claim_id: Optional[str] = None,
        min_similarity: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Semantic vector search across historical claim memories, filtered strictly by insurance category.
        """
        query_emb = await generate_embedding(query)
        stmt = select(ClaimMemory, Claim).outerjoin(Claim, ClaimMemory.claim_id == Claim.id)

        if exclude_claim_id:
            stmt = stmt.where(ClaimMemory.claim_id != exclude_claim_id)

        if category and category.lower() != "all":
            stmt = stmt.where(
                (Claim.category.ilike(category)) | (Claim.id == None)
            )

        res = await db.execute(stmt)
        rows = res.all()

        results = []
        for mem, claim in rows:
            emb = mem.embedding or []
            sim = _cosine_similarity(query_emb, emb)
            classification = "similar_case" if (claim and claim.category and claim.category.lower() == (category or "").lower()) else "historical_context"
            results.append({
                "memory_id": mem.id,
                "claim_id": claim.id if claim else mem.claim_id,
                "claim_number": claim.claim_number if claim else mem.claim_id,
                "claim_category": claim.category if claim else "General",
                "classification": classification,
                "memory_type": mem.memory_type,
                "memory_key": mem.memory_key,
                "memory_value": mem.memory_value,
                "source_agent": mem.source_agent,
                "confidence_score": mem.confidence_score,
                "similarity_score": round(sim, 4),
                "created_at": mem.created_at.isoformat() if mem.created_at else ""
            })

        # Sort descending by vector cosine similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        filtered = [r for r in results if r["similarity_score"] >= min_similarity]
        return filtered[:top_k] if filtered else results[:top_k]
