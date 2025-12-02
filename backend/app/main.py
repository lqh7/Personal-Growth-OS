"""
FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import json

from app.core.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    print("Initializing Personal Growth OS...")

    # Try to initialize database (non-critical for settings endpoints)
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize database: {e}")
        print("Settings endpoints will still work, but other features may be unavailable")

    # Initialize LangGraph PostgreSQL Checkpointer for chat persistence
    from app.core.langgraph_checkpoint import init_checkpointer
    try:
        await init_checkpointer()
        print("LangGraph Checkpointer initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize Checkpointer: {e}")
        print("Chat history persistence may not work correctly")

    # Initialize task reminder scheduler
    from app.core.scheduler import init_scheduler, shutdown_scheduler
    try:
        init_scheduler()
        print("Task scheduler initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize scheduler: {e}")
        print("Task reminders may not work correctly")

    yield

    # Shutdown
    try:
        shutdown_scheduler()
    except:
        pass

    # Shutdown LangGraph Checkpointer
    from app.core.langgraph_checkpoint import shutdown_checkpointer
    try:
        await shutdown_checkpointer()
    except:
        pass

    print("Shutting down Personal Growth OS...")


# Custom JSONResponse with explicit UTF-8 encoding
class UTF8JSONResponse(JSONResponse):
    """JSONResponse that ensures UTF-8 encoding for Chinese characters."""
    def render(self, content: any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,  # Critical: Don't escape non-ASCII characters
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Personal Growth OS - Your Second Brain for Accelerated Growth",
    version="0.1.0 (MVP)",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse,  # Use custom UTF-8 response
)

# Middleware to ensure UTF-8 response headers
@app.middleware("http")
async def add_utf8_header(request: Request, call_next):
    """Add UTF-8 content-type header to all JSON responses."""
    response = await call_next(request)
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

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
from app.api.endpoints import tasks, notes, projects, attachments, links, chat, settings as settings_router

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["attachments"])
app.include_router(links.router, prefix="/api/links", tags=["links"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])

# TODO: Additional routers to be implemented
# from app.api.endpoints import review
# app.include_router(review.router, prefix="/api/review", tags=["review"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

