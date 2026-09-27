import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.core.cloud_embedding import generate_embedding, generate_embeddings_batch
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

def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks cleanly around words/sentences."""
    if not text:
        return []
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1
        if current_length >= chunk_size:
            chunk_str = " ".join(current_chunk)
            chunks.append(chunk_str)
            # Overlap: keep last few words
            overlap_words = current_chunk[-max(1, int(len(current_chunk) * (overlap / chunk_size))):]
            current_chunk = list(overlap_words)
            current_length = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

class KnowledgeService:
    @staticmethod
    async def ingest_document(
        db: AsyncSession,
        title: str,
        content: str,
        document_type: str = "policy",
        source_file: Optional[str] = None,
        policy_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeDocument:
        """
        Ingest a policy or guidelines document, chunk it, embed chunks, and save to PostgreSQL.
        Links document to specific policy_number if provided.
        """
        meta = metadata or {}

        # Extract policy_number if not provided
        if not policy_number:
            import re
            m = re.search(r'(DEV-[A-Z]+-\d+|POL-[A-Z]+-\d+|POL-\d+)', f"{title} {source_file or ''}")
            if m:
                policy_number = m.group(1)
            elif title and not title.endswith('.pdf') and ' ' not in title:
                policy_number = title

        if policy_number:
            meta["policy_number"] = policy_number

        doc = KnowledgeDocument(
            title=title,
            document_type=document_type,
            source_file=source_file,
            policy_number=policy_number,
            metadata_json=meta
        )
        db.add(doc)
        await db.flush()

        # Ensure Policy record exists in policies table
        if policy_number:
            from app.models.policy import Policy
            from app.models.customer import Customer

            pol_stmt = select(Policy).where(Policy.policy_number == policy_number)
            pol_res = await db.execute(pol_stmt)
            existing_pol = pol_res.scalar_one_or_none()

            if not existing_pol:
                cust_email = meta.get("email")
                cust_name = meta.get("policyholder") or meta.get("customer_name")
                target_cust = None

                if cust_email:
                    cust_res = await db.execute(select(Customer).where(Customer.email == cust_email))
                    target_cust = cust_res.scalar_one_or_none()

                if not target_cust and cust_name:
                    cust_res = await db.execute(select(Customer).where(Customer.name.ilike(f"%{cust_name}%")))
                    target_cust = cust_res.scalar_one_or_none()

                if not target_cust:
                    cust_stmt_any = select(Customer).where(Customer.email.ilike(f"%{policy_number.lower()}%"))
                    cust_res_any = await db.execute(cust_stmt_any)
                    target_cust = cust_res_any.scalar_one_or_none()

                if target_cust:
                    doc_type_lower = (document_type or "").lower()
                    doc_title_lower = (title or "").lower()
                    if "health" in doc_type_lower or "health" in doc_title_lower:
                        category = "Health"
                        cov_limit = 750000.00
                        deductible = 1000.00
                    elif "home" in doc_type_lower or "property" in doc_type_lower or "home" in doc_title_lower:
                        category = "Home"
                        cov_limit = 500000.00
                        deductible = 2500.00
                    elif "travel" in doc_type_lower or "travel" in doc_title_lower:
                        category = "Travel"
                        cov_limit = 100000.00
                        deductible = 250.00
                    else:
                        category = "Vehicle"
                        cov_limit = 50000.00
                        deductible = 500.00

                    new_pol = Policy(
                        policy_number=policy_number,
                        category=category,
                        start_date="2025-01-01",
                        end_date="2027-12-31",
                        premium_status="Paid",
                        coverage_limit=cov_limit,
                        deductible=deductible,
                        active_claims_count=0,
                        customer_id=target_cust.id
                    )
                    db.add(new_pol)
                    await db.flush()
                    logger.info(f"Ingest auto-created Policy '{policy_number}' for customer '{target_cust.name}' in PostgreSQL.")


        clean_content = (content or "").replace('\x00', '')
        text_chunks = _chunk_text(clean_content, chunk_size=500, overlap=50)
        embeddings = await generate_embeddings_batch(text_chunks)

        for idx, (chunk_text, emb) in enumerate(zip(text_chunks, embeddings)):
            clean_chunk = chunk_text.replace('\x00', '')
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=clean_chunk,
                embedding=emb,
                metadata_json={"title": title, "document_type": document_type, "policy_number": policy_number}
            )
            db.add(chunk)

        await db.commit()
        logger.info(f"Ingested KnowledgeDocument '{title}' ({doc.id}) for policy '{policy_number}' with {len(text_chunks)} chunks.")
        return doc, len(text_chunks)

    @staticmethod
    async def search_knowledge(
        db: AsyncSession,
        query: str,
        top_k: int = 4,
        document_type: Optional[str] = None,
        policy_number: Optional[str] = None,
        min_similarity: float = 0.25
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant policy chunks using vector cosine similarity.
        If policy_number is specified, strictly filter by policy_number so no another customer's
        or generic sample policy is incorrectly substituted.
        """
        query_emb = await generate_embedding(query)
        
        stmt = select(KnowledgeChunk, KnowledgeDocument).join(
            KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id
        ).where(KnowledgeDocument.is_active == True)

        if document_type and document_type.lower() != "all":
            stmt = stmt.where(
                (KnowledgeDocument.document_type.ilike(document_type)) |
                (KnowledgeDocument.document_type == "policy")
            )

        if policy_number:
            from sqlalchemy import or_
            clean_pol = policy_number.strip()
            clean_pol_no_hyphen = clean_pol.replace("-", "")
            stmt = stmt.where(
                or_(
                    KnowledgeDocument.policy_number.ilike(f"%{clean_pol}%"),
                    KnowledgeDocument.policy_number.ilike(f"%{clean_pol_no_hyphen}%"),
                    KnowledgeDocument.title.ilike(f"%{clean_pol}%"),
                    KnowledgeDocument.title.ilike(f"%{clean_pol_no_hyphen}%"),
                    KnowledgeDocument.source_file.ilike(f"%{clean_pol}%"),
                    KnowledgeDocument.source_file.ilike(f"%{clean_pol_no_hyphen}%"),
                    KnowledgeChunk.content.ilike(f"%{clean_pol}%"),
                    KnowledgeChunk.content.ilike(f"%{clean_pol_no_hyphen}%")
                )
            )

        res = await db.execute(stmt)
        rows = res.all()

        results = []
        query_upper = query.upper()
        target_pol_clean = (policy_number or "").strip().upper().replace("-", "")

        for chunk, doc in rows:
            emb = chunk.embedding or []
            sim = _cosine_similarity(query_emb, emb)

            doc_pol_clean = (doc.policy_number or "").strip().upper().replace("-", "")
            doc_title_clean = (doc.title or "").strip().upper().replace("-", "")
            doc_src_clean = (doc.source_file or "").strip().upper().replace("-", "")

            # If this document is specifically for the requested policy, boost similarity score so its clauses are selected
            if target_pol_clean and (
                target_pol_clean in doc_pol_clean or
                target_pol_clean in doc_title_clean or
                target_pol_clean in doc_src_clean
            ):
                sim = max(sim, 0.85)

            # Keyword / Identifier boost: if query explicitly mentions title, policy code, or filename
            doc_id_str = f"{doc.title} {doc.policy_number or ''} {doc.source_file or ''}".upper()
            for token in query_upper.split():
                cleaned_token = token.strip("?,.:;!'\"()")
                if len(cleaned_token) >= 4 and cleaned_token in doc_id_str:
                    sim = max(sim, 0.75)
                    break

            effective_min = 0.05 if (policy_number and (target_pol_clean in doc_pol_clean or target_pol_clean in doc_title_clean)) else min_similarity

            if sim >= effective_min:
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "document_type": doc.document_type,
                    "policy_number": doc.policy_number or policy_number,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "similarity_score": round(sim, 4),
                    "source_file": doc.source_file
                })

        # Sort by similarity score descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]



    @staticmethod
    async def list_documents(db: AsyncSession) -> List[KnowledgeDocument]:
        try:
            stmt = select(KnowledgeDocument).options(selectinload(KnowledgeDocument.chunks)).order_by(KnowledgeDocument.id.desc())
            res = await db.execute(stmt)
            return list(res.scalars().all())
        except Exception as e:
            logger.warning(f"list_documents query warning: {e}")
            stmt = select(KnowledgeDocument)
            res = await db.execute(stmt)
            return list(res.scalars().all())


    @staticmethod
    async def delete_document(db: AsyncSession, document_id: str) -> bool:
        stmt = delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0
