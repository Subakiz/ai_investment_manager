"""
FastAPI application for AlphaGen Investment Platform
"""
from datetime import datetime
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from ..config.settings import config

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="AlphaGen Personal Investment Platform API",
        description="AI-powered investment platform API for Indonesian market",
        version="1.0.0"
    )

    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup"""
        print("Starting AlphaGen API server")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        print("Shutting down AlphaGen API server")

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "AlphaGen Personal Investment Platform API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/config")
    async def get_config():
        """Get application configuration (non-sensitive values only)"""
        return {
            "environment": config.ENVIRONMENT,
            "log_level": config.LOG_LEVEL,
            "timezone": config.TZ,
            "lq45_update_time": config.LQ45_UPDATE_TIME,
            "news_update_time": config.NEWS_UPDATE_TIME
        }

def run_server():
    """Run the FastAPI server if dependencies are available"""
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        return
    
    try:
        import uvicorn
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=config.ENVIRONMENT == "development"
        )
    except ImportError:
        print("uvicorn not available. Install with: pip install uvicorn")

if __name__ == "__main__":
    run_server()