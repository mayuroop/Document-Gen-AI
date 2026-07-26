"""
FastAPI main application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import connect_db, close_db
from app.routes import projects, documents
from app.utils.logger import setup_logging
from app.services.ai_service import ai_service

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle - startup and shutdown."""
    # Startup
    logger.info("🚀 Starting AI Documentation Generator API...")
    await connect_db()

    # Check Ollama
    ollama_ok = await ai_service.check_health()
    if ollama_ok:
        logger.info(f"🤖 Ollama model '{settings.ollama_model}' is ready")
    else:
        logger.warning(
            f"⚠️  Ollama model '{settings.ollama_model}' not found. "
            f"Run: ollama pull {settings.ollama_model}"
        )

    yield

    # Shutdown
    await close_db()
    logger.info("👋 Application shutdown complete")


app = FastAPI(
    title="AI Documentation Generator",
    description="Generate professional documentation from GitHub repositories using AI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(projects.router)
app.include_router(documents.router)


@app.get("/api/health")
async def health_check():
    """API health check."""
    ollama_ok = await ai_service.check_health()
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "disconnected",
        "ollama_model": settings.ollama_model,
        "version": "1.0.0",
    }


@app.get("/api")
async def root():
    """Root redirect info."""
    return {
        "message": "AI Documentation Generator API",
        "docs": "/docs",
        "health": "/api/health",
    }
