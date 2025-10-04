"""
Zaik - AI-Powered Text Adventure Game
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db import init_db, close_db
from .llm import close_llm_service, get_llm_service
from .routes import game


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Startup
    init_db()
    yield
    # Shutdown
    await close_llm_service()
    close_db()


app = FastAPI(
    title="Zaik API",
    description="Backend API for Zaik text adventure game",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(game.router)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Welcome to Zaik API",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint with LLM service status"""
    # llm_service = get_llm_service()
    # llm_status = await llm_service.health_check()

    return {
        "status": "healthy",
        "database": "connected",
        # "llm": llm_status
    }
