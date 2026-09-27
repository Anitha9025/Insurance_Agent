from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Configured CORS origins: {settings.CORS_ORIGINS}")

    # Initialize / Auto-create missing database tables in PostgreSQL
    try:
        from sqlalchemy import text
        from app.core.database import engine, Base
        import app.models  # Register all ORM models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS policy_number VARCHAR(64);"))
            await conn.execute(text("ALTER TABLE claims ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'INR';"))
        logger.info("PostgreSQL database tables initialized successfully.")

    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")

    yield
    # Shutdown sequence
    logger.info("Shutting down Insurance Claim Backend service")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS Middleware
cors_origins = [str(o) for o in settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]
if not cors_origins or cors_origins == ["*"]:
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Register API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
