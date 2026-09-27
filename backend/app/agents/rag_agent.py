from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.knowledge_service import KnowledgeService
from app.core.cloud_llm import generate_text
from app.core.logging import logger

class RAGKnowledgeAgent:
    """
    RAG Agent responsible for querying policy documents and retrieving grounded knowledge with citations.
    """

    @staticmethod
    async def query_policy_knowledge(
        db: AsyncSession,
        query: str,
        category: Optional[str] = None,
        policy_number: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[RAG Knowledge Agent] Processing policy query for policy '{policy_number}': '{query}'")
        
        # 1. Retrieve top matching knowledge chunks strictly filtered by policy_number
        chunks = await KnowledgeService.search_knowledge(
            db=db,
            query=query,
            top_k=4,
            document_type=category if (category and category.lower() != "all") else None,
            policy_number=policy_number
        )


        if not chunks:
            msg = (
                f"Customer-specific policy document is unavailable for policy number '{policy_number}' in PostgreSQL Knowledge Base. "
                "The system cannot make policy coverage determinations using another customer's generic policy. Manual officer verification required."
                if policy_number else
                "No specific policy clause was found matching your query in the active repository."
            )
            return {
                "policy_number": policy_number or "UNSPECIFIED",
                "policy_id": None,
                "customer_id": None,
                "document_found": False,
                "document_id": None,
                "policy_match": False,
                "category_match": False,
                "retrieval_confidence": 0.0,
                "relevant_clauses": [],
                "coverage_status": "policy_unavailable",
                "missing_information": [f"Policy document for '{policy_number}' unavailable in RAG Knowledge Base."],
                "manual_review_required": True,
                "answer": msg,
                "citations": [],
                "confidence": 0.0,
                "is_grounded": False,
                "uncertainty_flag": True,
                "policy_document_available": False,
                "policy_clauses_applied": []
            }

        # Build context from retrieved chunks
        context_str = "\n\n".join([
            f"--- Document: {c['document_title']} (Chunk #{c['chunk_index']}, Score: {c['similarity_score']}) ---\n{c['content']}"
            for c in chunks
        ])

        system_prompt = (
            "You are a Senior Insurance Policy Analyst AI. Your answers MUST be strictly grounded in the "
            "provided Policy Knowledge Context. Cite the exact document title and details. If the context does "
            "not contain enough information, state clearly what is missing."
        )

        prompt = f"""Policy Knowledge Context:
{context_str}

User / Agent Query: {query}

Provide a concise, grounded analysis explaining how the policy clauses apply. Include explicit citations."""

        llm_response = await generate_text(prompt=prompt, system_prompt=system_prompt, temperature=0.1)

        citations = [
            {
                "document_id": c["document_id"],
                "document_title": c["document_title"],
                "chunk_index": c["chunk_index"],
                "similarity_score": c["similarity_score"],
                "snippet": c["content"][:150] + "..."
            }
            for c in chunks
        ]

        top_score = max(c["similarity_score"] for c in chunks) if chunks else 0.0
        doc_id = chunks[0]["document_id"] if chunks else None

        return {
            "policy_number": policy_number or (chunks[0].get("policy_number") if chunks else "UNKNOWN"),
            "policy_id": doc_id,
            "customer_id": None,
            "document_found": True,
            "document_id": doc_id,
            "policy_match": True,
            "category_match": True if (not category or category.lower() in (chunks[0].get("document_type") or "").lower()) else False,
            "retrieval_confidence": round(float(top_score), 2),
            "relevant_clauses": [c["content"] for c in chunks],
            "coverage_status": "verified" if top_score >= 0.35 else "unverified",
            "missing_information": [] if top_score >= 0.35 else ["Low similarity match on policy clauses"],
            "manual_review_required": top_score < 0.35,
            "answer": llm_response,
            "citations": citations,
            "confidence": round(float(top_score * 100), 1),
            "is_grounded": top_score >= 0.35,
            "uncertainty_flag": top_score < 0.35,
            "policy_document_available": True,
            "policy_clauses_applied": [c["document_title"] for c in chunks]
        }
