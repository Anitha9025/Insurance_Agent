from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthCheckResponse, DatabaseHealth
from app.core.logging import logger

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Backend Health Check",
    description="Returns backend service health status, database connectivity status, and service metadata."
)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "disconnected"
    db_driver = "postgresql"
    db_error = None

    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "connected"
            if db.bind:
                db_driver = db.bind.dialect.name
    except Exception as e:
        logger.warning(f"Health check database ping failed: {str(e)}")
        db_error = str(e)

    return HealthCheckResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment="development" if settings.DEBUG else "production",
        database=DatabaseHealth(
            status=db_status,
            database_type=db_driver,
            error=db_error
        ),
        services={
            "ollama": settings.OLLAMA_BASE_URL,
            "chroma_db": settings.CHROMA_PERSIST_DIR
        }
    )
