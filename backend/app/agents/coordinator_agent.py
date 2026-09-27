import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import claim_service
from app.services.audit_service import create_audit_log
from app.schemas.audit_log import AuditLogCreate
from app.models.agent_step import AIAgentStep
from app.models.fraud_assessment import FraudAssessment
from app.models.recommendation_record import RecommendationRecord
from app.agents.state import (
    ClaimWorkflowState,
    AgentExecutionMeta,
    IntakeAgentResult,
    CustomerVerificationResult,
    DocumentAnalysisResult,
    PolicyValidationResult,
    ClaimHistoryResult
)
from app.agents.intake_agent import ClaimIntakeAgent
from app.agents.customer_verification_agent import CustomerVerificationAgent
from app.agents.document_analysis_agent import DocumentAnalysisAgent
from app.agents.policy_validation_agent import PolicyValidationAgent
from app.agents.claim_history_agent import ClaimHistoryAgent
from app.agents.rag_agent import RAGKnowledgeAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.evidence_normalization_agent import EvidenceNormalizationAgent
from app.agents.fraud_detection_agent import FraudDetectionAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.tools import (
    get_claim_by_id,
    get_customer_by_id,
    get_policy_by_number,
    get_customer_claims_history,
    get_claim_documents
)
from app.core.logging import logger

class CoordinatorAgent:
    """Coordinator Agent responsible for orchestrating the Phase 5 multi-agent claim analysis workflow.
    Controls execution flow via shared state (`ClaimWorkflowState`), executes independent sub-agents in parallel,
    records DB audit steps, and handles non-blocking agent failures without fabricating fake outcomes.
    """

    @staticmethod
    async def run_workflow(db: AsyncSession, claim_id: str) -> ClaimWorkflowState:
        workflow_start_time = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        logger.info(f"CoordinatorAgent starting multi-agent workflow for claim ID: {claim_id}")

        # 1. Fetch Claim Record & Context from Database
        claim_obj = await claim_service.get_claim_by_id(db, claim_id)
        
        if not claim_obj:
            logger.warning(f"CoordinatorAgent workflow halted: Claim '{claim_id}' not found in database.")
            state = ClaimWorkflowState(
                claim_id=claim_id,
                workflow_status="failed",
                errors=[f"Claim '{claim_id}' not found in database."],
                intake_analysis=IntakeAgentResult(
                    claim_id=claim_id,
                    claim_data_available=False,
                    missing_information=["claim_record_missing"],
                    warnings=["Claim not found in PostgreSQL."]
                )
            )
            return state

        # Convert SQLAlchemy ORM models to dictionary snapshots for workflow state
        claim_dict = CoordinatorAgent._serialize_claim_orm(claim_obj)
        customer_dict = CoordinatorAgent._serialize_customer_orm(claim_obj.customer) if claim_obj.customer else None
        policy_dict = CoordinatorAgent._serialize_policy_orm(claim_obj.policy) if claim_obj.policy else None
        documents_dict = [CoordinatorAgent._serialize_document_orm(d) for d in claim_obj.documents] if claim_obj.documents else []

        # Load customer policy document extracted fields from Knowledge Base / policy_service if available
        if policy_dict and claim_obj.policy_number:
            try:
                from app.services.policy_service import verify_policy
                pol_verif = await verify_policy(db, claim_obj.policy_number, claim_obj.incident_date)
                if pol_verif and pol_verif.get("specific_details"):
                    policy_dict["document_extracted_fields"] = pol_verif["specific_details"]
            except Exception as pol_err:
                logger.warning(f"CoordinatorAgent: Policy document extraction lookup warning: {pol_err}")

        # 2. Initialize Shared Workflow State
        state = ClaimWorkflowState(
            claim_id=str(claim_obj.id),
            customer_id=str(claim_obj.customer_id) if claim_obj.customer_id else None,
            policy_number=str(claim_obj.policy_number) if claim_obj.policy_number else None,
            claim_data=claim_dict,
            customer_data=customer_dict,
            policy_data=policy_dict,
            documents_data=documents_dict,
            workflow_status="in_progress"
        )

        # Record Initial Workflow Audit Log
        await create_audit_log(
            db,
            AuditLogCreate(
                timestamp=now_iso,
                claim_id=str(claim_obj.id),
                claim_number=str(claim_obj.claim_number),
                actor_type="AI Agent",
                actor_name="Coordinator Agent",
                action="Phase 5 Workflow Started",
                details=f"Initiated multi-agent analysis workflow for claim {claim_obj.claim_number}."
            )
        )

        # 3. STEP 1: Execute Claim Intake Agent (Sequential / Deterministic Prerequisite)
        intake_start = time.time()
        try:
            intake_res = ClaimIntakeAgent.analyze(state.claim_data, state.documents_data)
            state.intake_analysis = intake_res
            state.completed_agents.append("Claim Intake Agent")
            
            if intake_res.missing_information:
                state.warnings.extend([f"Intake Missing: {m}" for m in intake_res.missing_information])

            duration = round((time.time() - intake_start) * 1000, 2)
            state.agent_meta["Claim Intake Agent"] = AgentExecutionMeta(
                agent_name="Claim Intake Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=[f"Submitted Claim Amount: ${intake_res.claim_amount:,.2f}" if intake_res.claim_amount else "Claim amount unprovided"]
            )
            await CoordinatorAgent._save_agent_step_db(db, str(claim_obj.id), "Intake Agent", "Completed", duration, f"Parsed claim metadata ({intake_res.claim_type}).")

        except Exception as e:
            logger.error(f"CoordinatorAgent: Claim Intake Agent error: {str(e)}")
            state.errors.append(f"Claim Intake Agent failed: {str(e)}")
            state.agent_meta["Claim Intake Agent"] = AgentExecutionMeta(
                agent_name="Claim Intake Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

        # 4. Controlled DB Tools Execution (Sequential DB lookups)
        try:
            tool_res_claim = await get_claim_by_id(db, str(claim_obj.id))
            if tool_res_claim.success and tool_res_claim.data:
                state.db_tool_calls.append(tool_res_claim.model_dump())
            if claim_obj.customer_id:
                tool_res_cust = await get_customer_by_id(db, str(claim_obj.customer_id))
                if tool_res_cust.success and tool_res_cust.data:
                    state.db_tool_calls.append(tool_res_cust.model_dump())
            if claim_obj.policy_number:
                tool_res_pol = await get_policy_by_number(db, str(claim_obj.policy_number))
                if tool_res_pol.success and tool_res_pol.data:
                    state.db_tool_calls.append(tool_res_pol.model_dump())
        except Exception as tool_err:
            logger.warning(f"Controlled DB tool lookup warning: {tool_err}")

        # 5. STEP 2: Execute In-Memory Independent Agents in Parallel (Customer, Document, Policy)
        cust_task = asyncio.create_task(CoordinatorAgent._run_customer_verification(state))
        doc_task = asyncio.create_task(CoordinatorAgent._run_document_analysis(state))
        pol_task = asyncio.create_task(CoordinatorAgent._run_policy_validation(state))
        await asyncio.gather(cust_task, doc_task, pol_task, return_exceptions=True)

        # 6. Execute DB-dependent Agents Sequentially to avoid asyncpg connection locks
        await CoordinatorAgent._run_claim_history(db, state)
        await CoordinatorAgent._run_rag_knowledge(db, state)
        await CoordinatorAgent._run_memory_agent(db, state)

        # 7. PHASE 7: Evidence Normalization → Fraud Detection → Recommendation
        await CoordinatorAgent._run_evidence_normalization(state)
        await CoordinatorAgent._run_fraud_detection(state)
        await CoordinatorAgent._run_recommendation(db, state)

        # Record DB Steps & Audit Logs for parallel and sequential agent outcomes
        for agent_name, meta in state.agent_meta.items():
            if agent_name != "Claim Intake Agent":
                step_status = "Completed" if meta.status == "completed" else "Failed"
                summary_text = "; ".join(meta.evidence[:2]) if meta.evidence else ("; ".join(meta.errors) if meta.errors else "Executed")
                await CoordinatorAgent._save_agent_step_db(db, str(claim_obj.id), agent_name, step_status, meta.duration_ms, summary_text)

        # 5. STEP 3: Aggregate Workflow Status & Errors
        if len(state.errors) > 0 and len(state.completed_agents) == 0:
            state.workflow_status = "failed"
        else:
            state.workflow_status = "completed"

        total_duration = round((time.time() - workflow_start_time) * 1000, 2)
        logger.info(
            f"CoordinatorAgent workflow finished for claim '{claim_id}' in {total_duration}ms: "
            f"status={state.workflow_status}, completed_agents={state.completed_agents}, errors={len(state.errors)}"
        )

        # Final Workflow Audit Log
        await create_audit_log(
            db,
            AuditLogCreate(
                timestamp=datetime.now(timezone.utc).isoformat(),
                claim_id=str(claim_obj.id),
                claim_number=str(claim_obj.claim_number),
                actor_type="AI Agent",
                actor_name="Coordinator Agent",
                action="Phase 5 Workflow Completed",
                details=f"Completed multi-agent workflow in {total_duration}ms. Status: '{state.workflow_status}'."
            )
        )

        return state

    @staticmethod
    async def _run_customer_verification(state: ClaimWorkflowState):
        start = time.time()
        try:
            res = CustomerVerificationAgent.verify(state.customer_data, state.claim_data)
            state.customer_verification = res
            state.completed_agents.append("Customer Verification Agent")
            duration = round((time.time() - start) * 1000, 2)

            evidence = [f"Verified: {m}" for m in res.matched_fields]
            if res.mismatches:
                evidence.extend([f"Mismatch in {mm.field}" for mm in res.mismatches])

            state.agent_meta["Customer Verification Agent"] = AgentExecutionMeta(
                agent_name="Customer Verification Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Customer Verification Agent failed: {str(e)}")
            state.errors.append(f"Customer Verification Agent failed: {str(e)}")
            state.agent_meta["Customer Verification Agent"] = AgentExecutionMeta(
                agent_name="Customer Verification Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_document_analysis(state: ClaimWorkflowState):
        start = time.time()
        try:
            res = DocumentAnalysisAgent.analyze(state.documents_data, state.claim_data, state.customer_data, state.policy_data)
            state.document_analysis = res
            state.completed_agents.append("Document Analysis Agent")
            duration = round((time.time() - start) * 1000, 2)

            state.agent_meta["Document Analysis Agent"] = AgentExecutionMeta(
                agent_name="Document Analysis Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=res.evidence,
                warnings=res.uncertainties
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Document Analysis Agent failed: {str(e)}")
            state.errors.append(f"Document Analysis Agent failed: {str(e)}")
            state.agent_meta["Document Analysis Agent"] = AgentExecutionMeta(
                agent_name="Document Analysis Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_policy_validation(state: ClaimWorkflowState):
        start = time.time()
        try:
            res = PolicyValidationAgent.validate(state.policy_data, state.claim_data)
            state.policy_validation = res
            state.completed_agents.append("Policy Validation Agent")
            duration = round((time.time() - start) * 1000, 2)

            evidence = [chk.evidence for chk in res.checks if chk.status == "passed"]
            state.agent_meta["Policy Validation Agent"] = AgentExecutionMeta(
                agent_name="Policy Validation Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=evidence,
                warnings=res.issues
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Policy Validation Agent failed: {str(e)}")
            state.errors.append(f"Policy Validation Agent failed: {str(e)}")
            state.agent_meta["Policy Validation Agent"] = AgentExecutionMeta(
                agent_name="Policy Validation Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_claim_history(db: AsyncSession, state: ClaimWorkflowState):
        start = time.time()
        try:
            res = await ClaimHistoryAgent.analyze(db, state.customer_id, current_claim_id=state.claim_id)
            state.claim_history = res
            state.completed_agents.append("Claim History Agent")
            duration = round((time.time() - start) * 1000, 2)

            evidence = [f"Total Prior Claims: {res.total_previous_claims}", f"Approved Prior: {res.approved_claims_count}"]
            state.agent_meta["Claim History Agent"] = AgentExecutionMeta(
                agent_name="Claim History Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Claim History Agent failed: {str(e)}")
            state.errors.append(f"Claim History Agent failed: {str(e)}")
            state.agent_meta["Claim History Agent"] = AgentExecutionMeta(
                agent_name="Claim History Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_rag_knowledge(db: AsyncSession, state: ClaimWorkflowState):
        start = time.time()
        try:
            query = f"{state.claim_data.get('category', '')} policy {state.claim_data.get('title', '')} {state.claim_data.get('description', '')}"
            rag_res = await RAGKnowledgeAgent.query_policy_knowledge(
                db,
                query,
                category=state.claim_data.get('category'),
                policy_number=state.policy_number
            )
            state.rag_analysis = rag_res
            state.completed_agents.append("RAG Knowledge Agent")
            duration = round((time.time() - start) * 1000, 2)


            evidence = [f"Citations Found: {len(rag_res.get('citations', []))}", f"Grounded: {rag_res.get('is_grounded', False)}"]
            state.agent_meta["RAG Knowledge Agent"] = AgentExecutionMeta(
                agent_name="RAG Knowledge Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=evidence,
                warnings=["Low policy grounding confidence"] if rag_res.get("uncertainty_flag") else []
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: RAG Knowledge Agent failed: {str(e)}")
            state.errors.append(f"RAG Knowledge Agent failed: {str(e)}")
            state.agent_meta["RAG Knowledge Agent"] = AgentExecutionMeta(
                agent_name="RAG Knowledge Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_memory_agent(db: AsyncSession, state: ClaimWorkflowState):
        start = time.time()
        try:
            mem_res = await MemoryAgent.retrieve_relevant_memories(
                db=db,
                claim_id=state.claim_id,
                category=state.claim_data.get('category', 'Vehicle'),
                description=state.claim_data.get('description', '')
            )
            state.retrieved_memories = mem_res
            state.completed_agents.append("Memory Agent")
            duration = round((time.time() - start) * 1000, 2)

            evidence = [f"Similar Case Memories: {mem_res.get('similar_claims_count', 0)}"]
            state.agent_meta["Memory Agent"] = AgentExecutionMeta(
                agent_name="Memory Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Memory Agent failed: {str(e)}")
            state.errors.append(f"Memory Agent failed: {str(e)}")
            state.agent_meta["Memory Agent"] = AgentExecutionMeta(
                agent_name="Memory Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_evidence_normalization(state: ClaimWorkflowState):
        start = time.time()
        try:
            evidence_items = EvidenceNormalizationAgent.normalize(state)
            state.normalized_evidence = evidence_items
            state.completed_agents.append("Evidence Normalization Agent")
            duration = round((time.time() - start) * 1000, 2)
            state.agent_meta["Evidence Normalization Agent"] = AgentExecutionMeta(
                agent_name="Evidence Normalization Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=[f"Evidence Items Produced: {len(evidence_items)}"]
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Evidence Normalization Agent failed: {str(e)}")
            state.errors.append(f"Evidence Normalization Agent failed: {str(e)}")
            state.agent_meta["Evidence Normalization Agent"] = AgentExecutionMeta(
                agent_name="Evidence Normalization Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_fraud_detection(state: ClaimWorkflowState):
        start = time.time()
        try:
            assessment = FraudDetectionAgent.assess(state.normalized_evidence)
            state.fraud_assessment = assessment
            state.completed_agents.append("Fraud Detection Agent")
            duration = round((time.time() - start) * 1000, 2)
            state.agent_meta["Fraud Detection Agent"] = AgentExecutionMeta(
                agent_name="Fraud Detection Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=[
                    f"Risk Level: {assessment.risk_level.upper()}",
                    f"Risk Score: {assessment.rule_based_score:.1f}/100",
                    f"Signals Triggered: {assessment.signal_count}"
                ],
                warnings=[f"Disclaimer: {assessment.assessment_disclaimer[:80]}"]
            )
        except Exception as e:
            logger.error(f"CoordinatorAgent: Fraud Detection Agent failed: {str(e)}")
            state.errors.append(f"Fraud Detection Agent failed: {str(e)}")
            state.agent_meta["Fraud Detection Agent"] = AgentExecutionMeta(
                agent_name="Fraud Detection Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _run_recommendation(db: AsyncSession, state: ClaimWorkflowState):
        start = time.time()
        try:
            assessment = state.fraud_assessment
            if not assessment:
                # Create a minimal fallback assessment if fraud detection failed
                from app.agents.state import FraudRiskAssessmentResult
                assessment = FraudRiskAssessmentResult(
                    risk_level="unknown",
                    rule_based_score=0.0,
                    signal_count=0,
                    missing_information=["Fraud assessment was not completed."]
                )

            rec = await RecommendationAgent.recommend(state, state.normalized_evidence, assessment)
            state.recommendation = rec
            state.completed_agents.append("Recommendation Agent")
            duration = round((time.time() - start) * 1000, 2)

            state.agent_meta["Recommendation Agent"] = AgentExecutionMeta(
                agent_name="Recommendation Agent",
                status="completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=duration,
                evidence=[
                    f"Recommendation: {rec.recommendation_label}",
                    f"Confidence Basis: {rec.confidence_basis}",
                    f"Requires Human Review: {rec.requires_human_review}"
                ]
            )

            # Persist Phase 7 results to database
            await CoordinatorAgent._persist_fraud_assessment(db, state)
            await CoordinatorAgent._persist_recommendation_record(db, state)
            await CoordinatorAgent._sync_ai_recommendation(db, state)

        except Exception as e:
            logger.error(f"CoordinatorAgent: Recommendation Agent failed: {str(e)}")
            state.errors.append(f"Recommendation Agent failed: {str(e)}")
            state.agent_meta["Recommendation Agent"] = AgentExecutionMeta(
                agent_name="Recommendation Agent",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(e)]
            )

    @staticmethod
    async def _sync_ai_recommendation(db: AsyncSession, state: ClaimWorkflowState):
        """Syncs Phase 7 results into the relational AIRecommendation model for frontend Claim.ai_recommendation."""
        if not state.recommendation or not state.fraud_assessment:
            return
        try:
            from sqlalchemy import select
            from app.models.recommendation import AIRecommendation
            from app.models.claim import Claim

            r = state.recommendation
            f = state.fraud_assessment

            label_lower = (r.recommendation_label or r.recommendation or "").lower()
            if "approve" in label_lower:
                verdict = "Approve"
            elif "reject" in label_lower:
                verdict = "Reject"
            elif "more info" in label_lower or "request" in label_lower:
                verdict = "Request Additional Documents"
            else:
                verdict = "Review Required"

            # Query claim to calculate actual payout using claim amount & policy deductible
            claim_res = await db.execute(select(Claim).where(Claim.id == state.claim_id))
            claim_obj = claim_res.scalar_one_or_none()

            payout = 0.0
            if claim_obj:
                deductible = float(claim_obj.policy.deductible) if (claim_obj.policy and claim_obj.policy.deductible) else 0.0
                payout = max(0.0, float(claim_obj.claim_amount) - deductible)

            key_findings = r.risk_summary or r.policy_references or []
            if not key_findings and state.normalized_evidence:
                key_findings = [f"{e.evidence_type}: {e.value}" for e in state.normalized_evidence[:4]]

            ret_mems = [
                {"claimId": m.claim_id, "summary": m.memory_value, "similarityScore": m.confidence_score}
                for m in state.memories
            ] if state.memories else []

            ret_know = [
                {
                    "policyTitle": c.metadata_json.get("title", "Policy Clause") if c.metadata_json else "Policy Clause",
                    "sectionCode": c.metadata_json.get("policy_number", "POLICY") if c.metadata_json else "POLICY",
                    "clause": c.content
                }
                for c in state.knowledge_chunks
            ] if state.knowledge_chunks else []

            # Upsert
            existing_rec = await db.execute(select(AIRecommendation).where(AIRecommendation.claim_id == state.claim_id))
            old_rec = existing_rec.scalar_one_or_none()

            if old_rec:
                old_rec.verdict = verdict
                old_rec.fraud_risk_score = float(f.rule_based_score)
                old_rec.confidence_score = 0.0  # Mark uncalibrated score as 0.0 (Unavailable)
                old_rec.recommended_amount = payout
                old_rec.reasoning_summary = r.reasoning_summary
                old_rec.key_findings = key_findings
                old_rec.risk_flags = [s.signal_name for s in f.signals]
                old_rec.retrieved_memories = ret_mems
                old_rec.retrieved_knowledge = ret_know
            else:
                new_rec = AIRecommendation(
                    claim_id=state.claim_id,
                    verdict=verdict,
                    fraud_risk_score=float(f.rule_based_score),
                    confidence_score=0.0,
                    recommended_amount=payout,
                    reasoning_summary=r.reasoning_summary,
                    key_findings=key_findings,
                    risk_flags=[s.signal_name for s in f.signals],
                    retrieved_memories=ret_mems,
                    retrieved_knowledge=ret_know,
                    tool_calls=[]
                )
                db.add(new_rec)

            await db.flush()
            logger.info(f"Synced AIRecommendation for claim {state.claim_id}: verdict={verdict}, fraud_score={f.rule_based_score}, payout={payout}")
        except Exception as e:
            logger.warning(f"Failed to sync AIRecommendation: {str(e)}")


    @staticmethod
    async def _persist_fraud_assessment(db: AsyncSession, state: ClaimWorkflowState):
        """Persists the Phase 7 fraud assessment to the fraud_assessments table."""
        if not state.fraud_assessment:
            return
        try:
            a = state.fraud_assessment
            from sqlalchemy import select
            from app.models.fraud_assessment import FraudAssessment

            # Upsert: delete old if exists (unique on claim_id)
            existing = await db.execute(
                select(FraudAssessment).where(FraudAssessment.claim_id == state.claim_id)
            )
            old = existing.scalar_one_or_none()
            if old:
                await db.delete(old)
                await db.flush()

            fa = FraudAssessment(
                claim_id=state.claim_id,
                risk_level=a.risk_level,
                rule_based_score=a.rule_based_score,
                score_rule_version=a.score_rule_version,
                signal_count=a.signal_count,
                signals_json=[s.model_dump() for s in a.signals],
                supporting_evidence_json=a.supporting_evidence,
                contradictory_evidence_json=a.contradictory_evidence,
                missing_information_json=a.missing_information,
                uncertainties_json=a.uncertainties,
                normalized_evidence_json=[e.model_dump() for e in state.normalized_evidence],
                requires_human_review=a.requires_human_review,
                llm_provider=a.llm_provider,
                llm_model=a.llm_model,
                assessment_disclaimer=a.assessment_disclaimer,
                assessment_status="completed"
            )
            db.add(fa)
            await db.flush()
            logger.info(f"Phase 7 FraudAssessment persisted for claim {state.claim_id}")
        except Exception as e:
            logger.warning(f"Failed to persist fraud assessment: {str(e)}")
            try:
                await db.rollback()
            except Exception:
                pass

    @staticmethod
    async def _persist_recommendation_record(db: AsyncSession, state: ClaimWorkflowState):
        """Persists the Phase 7 recommendation to the recommendation_records table."""
        if not state.recommendation:
            return
        try:
            r = state.recommendation
            from sqlalchemy import select
            from app.models.recommendation_record import RecommendationRecord

            existing = await db.execute(
                select(RecommendationRecord).where(RecommendationRecord.claim_id == state.claim_id)
            )
            old = existing.scalar_one_or_none()
            if old:
                await db.delete(old)
                await db.flush()

            rr = RecommendationRecord(
                claim_id=state.claim_id,
                recommendation=r.recommendation,
                recommendation_label=r.recommendation_label,
                reasoning_summary=r.reasoning_summary,
                policy_references_json=r.policy_references,
                risk_summary_json=r.risk_summary,
                missing_information_json=r.missing_information,
                required_next_actions_json=r.required_next_actions,
                override_reason=r.override_reason,
                confidence_basis=r.confidence_basis,
                requires_human_review=r.requires_human_review,
                final_decision_made=r.final_decision_made,
                llm_provider=r.llm_provider,
                llm_model=r.llm_model,
                prompt_version=r.prompt_version
            )
            db.add(rr)
            await db.flush()
            logger.info(f"Phase 7 RecommendationRecord persisted for claim {state.claim_id}")
        except Exception as e:
            logger.warning(f"Failed to persist recommendation record: {str(e)}")
            try:
                await db.rollback()
            except Exception:
                pass

    @staticmethod
    async def _save_agent_step_db(db: AsyncSession, claim_id: str, agent_name: str, status: str, duration_ms: float, summary: str):

        try:
            step = AIAgentStep(
                claim_id=claim_id,
                agent_name=agent_name,
                status=status,
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=int(round(duration_ms)),
                output_summary=summary[:255]
            )
            db.add(step)
            await db.flush()
        except Exception as err:
            logger.warning(f"Failed to record agent step DB row: {str(err)}")
            try:
                await db.rollback()
            except Exception:
                pass

    # Helper serializers for ORM -> dict snapshots
    @staticmethod
    def _serialize_claim_orm(c) -> Dict[str, Any]:
        return {
            "id": str(c.id),
            "claim_number": str(c.claim_number),
            "title": str(c.title),
            "description": str(c.description),
            "category": str(c.category),
            "priority": str(c.priority),
            "is_emergency": bool(c.is_emergency),
            "status": str(c.status),
            "incident_date": str(c.incident_date) if c.incident_date else None,
            "incident_time": str(c.incident_time) if c.incident_time else None,
            "location": str(c.location) if c.location else None,
            "claim_amount": float(c.claim_amount) if c.claim_amount is not None else None,
            "customer_id": str(c.customer_id) if c.customer_id else None,
            "policy_number": str(c.policy_number) if c.policy_number else None
        }

    @staticmethod
    def _serialize_customer_orm(cust) -> Dict[str, Any]:
        return {
            "id": str(cust.id),
            "name": str(cust.name),
            "phone": str(cust.phone),
            "email": str(cust.email),
            "dob": str(cust.dob) if cust.dob else None,
            "address": str(cust.address) if cust.address else None,
            "national_id": str(cust.national_id) if cust.national_id else None,
            "member_since": str(cust.member_since) if cust.member_since else None,
            "risk_score": float(cust.risk_score) if cust.risk_score is not None else None
        }

    @staticmethod
    def _serialize_policy_orm(pol) -> Dict[str, Any]:
        return {
            "policy_number": str(pol.policy_number),
            "category": str(pol.category),
            "start_date": str(pol.start_date),
            "end_date": str(pol.end_date),
            "premium_status": str(pol.premium_status),
            "coverage_limit": float(pol.coverage_limit) if pol.coverage_limit is not None else None,
            "deductible": float(pol.deductible) if pol.deductible is not None else None,
            "customer_id": str(pol.customer_id)
        }

    @staticmethod
    def _serialize_document_orm(d) -> Dict[str, Any]:
        ocr_fields = []
        if hasattr(d, "ocr_fields") and d.ocr_fields:
            for o in d.ocr_fields:
                ocr_fields.append({
                    "field_name": str(o.field_name),
                    "extracted_value": str(o.extracted_value),
                    "confidence": float(o.confidence),
                    "status": str(o.status)
                })
        return {
            "id": str(d.id),
            "file_name": str(d.file_name),
            "file_path": str(d.file_path),
            "type": str(d.type),
            "category": str(d.category),
            "ocr_status": str(d.ocr_status),
            "verification_status": str(d.verification_status),
            "ocr_fields": ocr_fields
        }
