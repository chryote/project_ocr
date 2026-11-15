"""Main FastAPI application entrypoint.

Initializes FastAPI app, middleware, routers, exception handlers,
and OpenAPI documentation metadata.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import uvicorn

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import (
    AppException,
    FileSizeExceededError,
    ImageProcessingError,
    InvalidFileTypeError,
    OCRExecutionError,
)
from app.core.logging import logger
from app.schemas.api_response import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown routines."""
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENV}]")
    logger.info(f"Tesseract binary configured at: {settings.TESSERACT_CMD}")
    logger.info(f"Tessdata directory: {settings.TESSDATA_PREFIX}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Factory function for creating and configuring the FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "Hospitality Engineering Team",
            "email": "dev@hotel-ocr.local",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    @app.exception_handler(InvalidFileTypeError)
    async def invalid_file_type_handler(request: Request, exc: InvalidFileTypeError):
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content=ErrorResponse(
                error_code="INVALID_FILE_TYPE",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(FileSizeExceededError)
    async def file_size_handler(request: Request, exc: FileSizeExceededError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content=ErrorResponse(
                error_code="FILE_TOO_LARGE",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(ImageProcessingError)
    async def image_processing_handler(request: Request, exc: ImageProcessingError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error_code="IMAGE_PROCESSING_FAILED",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(OCRExecutionError)
    async def ocr_execution_handler(request: Request, exc: OCRExecutionError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponse(
                error_code="OCR_ENGINE_ERROR",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(AppException)
    async def domain_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error_code="PROCESSING_ERROR",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    # Mount API routers
    app.include_router(api_router)

    # Root redirect to documentation
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Global top-level health endpoint
    @app.get("/health", include_in_schema=False)
    async def global_health():
        return RedirectResponse(url="/api/v1/health")

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
