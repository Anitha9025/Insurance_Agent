import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.agents.coordinator_agent import CoordinatorAgent

async def main():
    async with AsyncSessionLocal() as db:
        # Run workflow on claim-101 or latest claim
        claim_id = "claim-101"
        print("==============================================================================================================")
        print(f"EXECUTING PHASE 5 MULTI-AGENT SWARM WORKFLOW FOR CLAIM: {claim_id}")
        print("==============================================================================================================")
        
        result = await CoordinatorAgent.run_workflow(db, claim_id)
        
        print("\n--- AGENT 1: CLAIM INTAKE AGENT OUTPUT ---")
        if result.intake_analysis:
            print(f"Is Valid Form: {result.intake_analysis.is_valid_form}")
            print(f"Categorization: {result.intake_analysis.categorization}")
            print(f"Priority Level: {result.intake_analysis.priority_level}")
            print(f"Documents Count: {result.intake_analysis.documents_submitted_count}")
            print("Intake Findings:", result.intake_analysis.findings)

        print("\n--- AGENT 2: CUSTOMER VERIFICATION AGENT OUTPUT ---")
        if result.customer_verification:
            print(f"Identity Verified: {result.customer_verification.identity_verified}")
            print(f"Risk Score: {result.customer_verification.risk_score}")
            print(f"Risk Level: {result.customer_verification.risk_level}")
            print("Customer Findings:", result.customer_verification.findings)

        print("\n--- AGENT 3: DOCUMENT ANALYSIS AGENT OUTPUT ---")
        if result.document_analysis:
            print(f"Documents Analyzed: {result.document_analysis.documents_analyzed}")
            print("Evidence List:")
            for ev in result.document_analysis.evidence:
                print(f"  • {ev}")
            print("Uncertainties/Mismatches:")
            for unc in result.document_analysis.uncertainties:
                print(f"  ⚠️ {unc}")

        print("\n--- AGENT 4: POLICY VALIDATION AGENT OUTPUT ---")
        if result.policy_validation:
            print(f"Policy Active: {result.policy_validation.policy_active}")
            print(f"Claim Covered: {result.policy_validation.claim_covered}")
            print(f"Coverage Limit: ${result.policy_validation.coverage_limit:,.2f}")
            print(f"Deductible: ${result.policy_validation.deductible:,.2f}")
            print(f"Max Payout Allowed: ${result.policy_validation.max_payout_allowed:,.2f}")
            print("Policy Findings:", result.policy_validation.findings)

        print("\n--- AGENT 5: CLAIM HISTORY AGENT OUTPUT ---")
        if result.claim_history:
            print(f"Past Claims Count: {result.claim_history.past_claims_count}")
            print(f"Total Past Claimed: ${result.claim_history.total_past_claimed:,.2f}")
            print(f"Frequency Risk Flag: {result.claim_history.frequency_risk_flag}")
            print("History Findings:", result.claim_history.findings)

        print("\n==============================================================================================================")
        print("FINAL COORDINATOR AGENT RECOMMENDATION & VERDICT")
        print("==============================================================================================================")
        if result.final_recommendation:
            rec = result.final_recommendation
            print(f"VERDICT: {rec.get('verdict')}")
            print(f"RECOMMENDED PAYOUT: ${rec.get('recommended_amount', 0):,.2f}")
            print(f"CONFIDENCE SCORE: {rec.get('confidence_score')}%")
            print(f"FRAUD RISK INDEX: {rec.get('fraud_risk_index')} / 100 ({rec.get('risk_level')})")
            print("REASONING SUMMARY:\n", rec.get('reasoning_summary'))
            print("\nKEY FINDINGS:")
            for kf in rec.get('key_findings', []):
                print(f"  • {kf}")

if __name__ == "__main__":
    asyncio.run(main())
