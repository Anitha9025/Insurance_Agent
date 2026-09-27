import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def cleanup_database_duplicates():
    async_url = settings.async_database_url or "postgresql+asyncpg://postgres:postgres_password@localhost:5432/insurance_claims_db"
    print("=" * 90)
    print("CLEANING UP DUPLICATE OCR ROWS IN POSTGRESQL DATABASE...")
    print("=" * 90)

    try:
        engine = create_async_engine(async_url)
        async with engine.begin() as conn:
            # Delete duplicate rows in ocr_fields table keeping only the latest row per (document_id, field_name)
            query = text("""
                DELETE FROM ocr_fields o1
                USING ocr_fields o2
                WHERE o1.id < o2.id
                  AND o1.document_id = o2.document_id
                  AND LOWER(TRIM(o1.field_name)) = LOWER(TRIM(o2.field_name));
            """)
            res = await conn.execute(query)
            print(f"✅ Successfully deleted duplicate rows from 'ocr_fields' table.")
            
        await engine.dispose()
        print("=" * 90)
    except Exception as e:
        print(f"Cleanup Note: {str(e)}")

if __name__ == "__main__":
    asyncio.run(cleanup_database_duplicates())
