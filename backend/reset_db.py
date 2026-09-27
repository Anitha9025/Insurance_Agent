import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.db.init_db import init_db

async def reset_database(reseed: bool = True):
    async_url = settings.async_database_url or "postgresql+asyncpg://postgres:postgres_password@localhost:5432/insurance_claims_db"
    print("=" * 80)
    print("CLEARING POSTGRESQL DATABASE RECORDS...")
    print("=" * 80)

    engine = create_async_engine(async_url)
    try:
        async with engine.begin() as conn:
            # Truncate all tables with CASCADE to wipe all records cleanly
            query = text("""
                TRUNCATE TABLE 
                    ocr_fields, 
                    claim_documents, 
                    agent_steps, 
                    ai_recommendations, 
                    audit_logs, 
                    claims, 
                    policies, 
                    customers 
                RESTART IDENTITY CASCADE;
            """)
            await conn.execute(query)
            print("✅ Successfully cleared all database records from PostgreSQL.")
            
        await engine.dispose()

        if reseed:
            print("\nSeeding initial clean baseline data...")
            async with AsyncSessionLocal() as session:
                await init_db(session)
            print("✅ Initial seed data recreated successfully.")

        print("=" * 80)
        print("DATABASE RESET COMPLETE!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")

if __name__ == "__main__":
    reseed_flag = "--no-reseed" not in sys.argv
    asyncio.run(reset_database(reseed=reseed_flag))
