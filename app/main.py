import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db
from app.routers import agent, tools, reviewer, patients

# Ensure SQLite tables exist
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    print(f"[*] Voice Agent Backend started on {settings.host}:{settings.port}")
    print(f"[*] Environment: {settings.environment}")
    print(f"[*] ElevenLabs Agent ID: {settings.agent_id}")
    yield

app = FastAPI(
    title="ElevenLabs Voice Agent Backend - Patient Registration",
    description="FastAPI backend to securely connect callers to ElevenLabs Patient Registration Agent with persistent SQLite database and REST API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(patients.router)
app.include_router(agent.router)
app.include_router(tools.router)
app.include_router(reviewer.router)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    """Serves the voice agent web caller interface."""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "agent_configured": bool(settings.agent_id),
        "api_key_configured": bool(settings.elevenlabs_api_key),
        "environment": settings.environment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
