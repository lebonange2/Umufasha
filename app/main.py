"""FastAPI application for LLM-powered personal assistant."""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import structlog

from app.deps import get_db, get_redis, get_llm_client, get_scheduler
from app.models import Base
from app.database import engine
from app.routes import (
    users,
    events,
    notifications,
    calendar,
    telephony,
    email,
    admin,
    webhooks,
    rsvp,
    testing,
    writer
)
from app.routes import writer_documents
from app.core.config import settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up appointment assistant")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.start()
        logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down appointment assistant")
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="LLM-Powered Personal Assistant",
    description="Personal assistant that calls or emails about appointments",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount writer static files (after build)
writer_static_path = "app/static/writer"
if os.path.exists(writer_static_path):
    app.mount("/writer-static", StaticFiles(directory=writer_static_path), name="writer-static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(telephony.router, prefix="/twilio", tags=["telephony"])
app.include_router(email.router, prefix="/email", tags=["email"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(webhooks.router, prefix="/hooks", tags=["webhooks"])
app.include_router(rsvp.router, prefix="/rsvp", tags=["rsvp"])
app.include_router(testing.router, prefix="/testing", tags=["testing"])
app.include_router(writer.router, tags=["writer"])
app.include_router(writer_documents.router, tags=["writer-documents"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - unified homepage."""
    return templates.TemplateResponse("homepage.html", {
        "request": request,
        "title": "AI Assistant - Unified Workspace"
    })


@app.get("/writer", response_class=HTMLResponse)
async def writer_page(request: Request):
    """Writer page - serve React app."""
    # Check if built files exist
    writer_index = os.path.join("app/static/writer", "index.html")
    if os.path.exists(writer_index):
        with open(writer_index, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        # Development mode - return a simple page that loads from Vite dev server
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Writing Assistant</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="http://localhost:5173/src/main.tsx"></script>
</body>
</html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # TODO: Implement actual metrics collection
    return {"status": "metrics endpoint"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
