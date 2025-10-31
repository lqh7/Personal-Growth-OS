"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    print("Initializing Personal Growth OS...")
    init_db()
    print("Database initialized")

    yield

    # Shutdown
    print("Shutting down Personal Growth OS...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Personal Growth OS - Your Second Brain for Accelerated Growth",
    version="0.1.0 (MVP)",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Personal Growth OS API is running",
        "version": "0.1.0 (MVP)",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "database": "connected"
    }


# Import and include routers
from app.api.endpoints import tasks, notes, projects

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

# TODO: Additional routers to be implemented
# from app.api.endpoints import chat, review
# app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
# app.include_router(review.router, prefix="/api/review", tags=["review"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
