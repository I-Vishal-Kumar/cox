"""
Cox Automotive AI Data Analytics Agent - Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.routes import router
from app.db.database import init_db, async_session
from app.db.seed_data import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting Cox Automotive AI Analytics Agent...")

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Initialize database
    await init_db()
    print("✓ Database initialized")

    # Check if we need to seed data
    db_path = "data/cox_automotive.db"
    should_seed = not os.path.exists(db_path) or os.path.getsize(db_path) < 1000

    if should_seed:
        print("📊 Seeding demo data...")
        async with async_session() as session:
            await seed_all(session)
        print("✓ Demo data seeded successfully")

    # Session management is handled by LangChain orchestrator
    # Sessions are stored in data/sessions directory
    print("✓ Session storage ready at data/sessions")

    yield

    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Cox Automotive AI Analytics Agent",
    description="AI-powered data analytics for automotive industry",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Cox Automotive AI Analytics Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
