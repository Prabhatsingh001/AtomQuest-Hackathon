"""FastAPI main application entry point."""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.database import engine

from app.routers import (
    auth,
    goals,
    approvals,
    checkins,
    admin,
    reports,
    users,
    departments,
)

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="AtomQuest Goal Portal API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(goals.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(checkins.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")


# Health endpoint
@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "detail": str(exc.detail),
            "code": "HTTP_ERROR",
        },
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "detail": exc.errors(),
            "code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "detail": str(exc)
            if settings.ENVIRONMENT == "development"
            else "An error occurred",
            "code": "INTERNAL_ERROR",
        },
    )


@app.on_event("startup")
async def startup():
    """Verify DB connection on startup."""
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
