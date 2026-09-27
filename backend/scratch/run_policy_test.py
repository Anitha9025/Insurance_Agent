import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import AsyncSessionLocal, engine, Base
from tests.test_policy_retrieval_workflow import (
    test_scenario_a_policy_found_with_document,
    test_scenario_b_policy_found_document_unavailable,
    test_scenario_c_policy_not_found,
    test_scenario_d_policy_expired
)
from app.db.init_db import init_db

async def main():
    print("=== STARTING POLICY RETRIEVAL & WORKFLOW TEST SCENARIOS ===")
    
    # 1. Initialize Tables & Seed Data
    async with AsyncSessionLocal() as db:
        await init_db(db)

    # 2. Run Test Scenario A
    async with AsyncSessionLocal() as db:
        print("\n--> Running Test Scenario A (Policy Found with Document)...")
        await test_scenario_a_policy_found_with_document(db)
        print("  ✓ Scenario A PASSED!")

    # 3. Run Test Scenario B
    async with AsyncSessionLocal() as db:
        print("\n--> Running Test Scenario B (Policy Found, Document Unavailable)...")
        await test_scenario_b_policy_found_document_unavailable(db)
        print("  ✓ Scenario B PASSED!")

    # 4. Run Test Scenario C
    async with AsyncSessionLocal() as db:
        print("\n--> Running Test Scenario C (Policy Not Found)...")
        await test_scenario_c_policy_not_found(db)
        print("  ✓ Scenario C PASSED!")

    # 5. Run Test Scenario D
    async with AsyncSessionLocal() as db:
        print("\n--> Running Test Scenario D (Policy Expired)...")
        await test_scenario_d_policy_expired(db)
        print("  ✓ Scenario D PASSED!")

    print("\n=== ALL 4 TEST SCENARIOS PASSED CLEANLY! ===")

if __name__ == "__main__":
    asyncio.run(main())
