from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import MemoryService
from app.core.cloud_llm import generate_text
from app.core.logging import logger

class MemoryAgent:
    """
    Memory Agent responsible for searching past claim memories and storing newly validated claim insights.
    """

    @staticmethod
    async def retrieve_relevant_memories(
        db: AsyncSession,
        claim_id: str,
        category: str,
        description: str
    ) -> Dict[str, Any]:
        logger.info(f"[Memory Agent] Retrieving category-isolated historical memories for claim '{claim_id}' (Category: {category})")
        
        search_query = f"{category} {description[:200]}"
        memories = await MemoryService.search_memories(
            db=db,
            query=search_query,
            category=category,
            top_k=5,
            exclude_claim_id=claim_id
        )

        if not memories:
            return {
                "summary": "No historical claim memories found matching this claim pattern and category.",
                "retrieved_memories": [],
                "similar_claims_count": 0,
                "recommendation_hint": "Process claim with standard validation rules."
            }

        context_str = "\n".join([
            f"- Claim {m['claim_number']} ({m['claim_category']}) [{m.get('classification', 'historical_context')}]: [{m['memory_type']}] {m['memory_key']} -> {m['memory_value']} (Similarity: {m['similarity_score']})"
            for m in memories
        ])

        system_prompt = (
            "You are an Insurance Memory & Case History AI Agent. "
            "IMPORTANT RULE: Historical claim memories are provided purely as contextual background or precedent hints. "
            "They MUST NOT be treated as current claim policy terms, nor force automatic approval or rejection of the current claim. "
            "Current claim policy clauses always supersede historical memories."
        )
        prompt = f"""Historical Claim Memories Found (Category: {category}):
{context_str}

Current Claim Category: {category}
Current Claim Description: {description}

Summarize key insights or precedents from these historical memories for the current claim as contextual reference only."""

        summary_text = await generate_text(prompt=prompt, system_prompt=system_prompt, temperature=0.2)

        return {
            "summary": summary_text,
            "retrieved_memories": memories,
            "similar_claims_count": len(memories),
            "recommendation_hint": "Precedents available from historical claim decisions in the same category."
        }

    @staticmethod
    async def save_claim_decision_memory(
        db: AsyncSession,
        claim_id: str,
        decision_status: str,
        recommendation_reasoning: str,
        source_agent: str = "CoordinatorAgent"
    ):
        logger.info(f"[Memory Agent] Saving decision memory for claim '{claim_id}' ({decision_status})")
        await MemoryService.add_memory(
            db=db,
            claim_id=claim_id,
            memory_type="decision_rationale",
            memory_key=f"status_{decision_status.lower()}",
            memory_value=recommendation_reasoning,
            confidence_score=1.0,
            source_agent=source_agent
        )
