"""Main FastAPI application for MedCompanion server."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from server.config import settings
from server.db import init_db
from server.services import medgemma_service, medasr_service
from server.services.system_prompts import clear_prompt_cache
from server.api.routes import chat, sessions, dicom, documents, speech
from server.api.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    # Startup
    print("Initializing MedCompanion server...")
    
    # Initialize database
    init_db()
    print("Database initialized")
    
    # Load model in background
    print("Loading MedGemma model...")
    medgemma_service.load_model()
    
    # Note: MedASR is loaded on-demand (lazy loading) when speech endpoint is first called
    print("MedASR model will be loaded on-demand when needed")
    
    yield
    
    # Shutdown
    print("Shutting down MedCompanion server...")
    
    # Clean up DICOM temp folders
    from server.api.routes.dicom import cleanup_all_temp_folders
    cleanup_all_temp_folders()


# Create FastAPI app
app = FastAPI(
    title="MedCompanion API",
    description="FastAPI server for MedGemma medical AI assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(dicom.router)
app.include_router(documents.router)
app.include_router(speech.router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        model_loaded=medgemma_service.model_loaded,
        version="1.0.0",
        medasr_loaded=medasr_service.model_loaded
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MedCompanion API Server",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/v1/admin/clear-prompt-cache")
async def clear_cache():
    """Clear the system prompt cache. Useful for development when updating prompts."""
    clear_prompt_cache()
    return {"status": "ok", "message": "Prompt cache cleared. New prompts will be loaded on next request."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload
    )
