from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import logger

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler for HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for request validation errors (HTTP 422)."""
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": 422,
                "message": "Validation Error",
                "details": exc.errors(),
                "path": str(request.url.path)
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all exception handler (HTTP 500)."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal Server Error",
                "path": str(request.url.path)
            }
        }
    )
