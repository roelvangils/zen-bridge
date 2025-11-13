"""HTTP API server for Zen Bridge / Inspekt CLI commands.

This server exposes all CLI commands as HTTP endpoints, allowing
browser automation and control via REST API calls.

Start the server with:
    uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000 --reload

Or use the CLI:
    zen api start
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from zen.services.bridge_executor import get_executor
from zen import __version__

# Create FastAPI app
app = FastAPI(
    title="Inspekt API",
    description="HTTP API for browser automation and control via command line",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware (allow all origins for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ConnectionError)
async def connection_error_handler(request, exc):
    """Handle bridge connection errors."""
    return JSONResponse(
        status_code=503,
        content={
            "ok": False,
            "error": f"Bridge server connection error: {str(exc)}",
            "detail": "Is the bridge server running? Start it with: zen server start",
        },
    )


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request, exc):
    """Handle command timeout errors."""
    return JSONResponse(
        status_code=504, content={"ok": False, "error": f"Command timeout: {str(exc)}"}
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    """Handle runtime errors from command execution."""
    return JSONResponse(status_code=500, content={"ok": False, "error": f"Runtime error: {str(exc)}"})


# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if API and bridge server are running."""
    executor = get_executor()
    bridge_running = executor.is_server_running()

    return {
        "api": "running",
        "api_version": __version__,
        "bridge_server": "running" if bridge_running else "stopped",
        "bridge_host": "127.0.0.1",
        "bridge_ports": {"http": 8765, "websocket": 8766},
    }


@app.get("/")
async def root():
    """API root endpoint with basic info and links."""
    return {
        "name": "Inspekt API",
        "version": __version__,
        "description": "HTTP API for browser automation commands",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "navigation": "/api/navigation/*",
            "extraction": "/api/extraction/*",
            "execution": "/api/execution/*",
            "interaction": "/api/interaction/*",
            "inspection": "/api/inspection/*",
            "selection": "/api/selection/*",
            "cookies": "/api/cookies/*",
        },
    }


# Import and register routers
from zen.app.api.routers import (
    navigation,
    execution,
    extraction,
    interaction,
    inspection,
    selection,
    cookies,
)

app.include_router(navigation.router, prefix="/api/navigation", tags=["Navigation"])
app.include_router(execution.router, prefix="/api/execution", tags=["Execution"])
app.include_router(extraction.router, prefix="/api/extraction", tags=["Extraction"])
app.include_router(interaction.router, prefix="/api/interaction", tags=["Interaction"])
app.include_router(inspection.router, prefix="/api/inspection", tags=["Inspection"])
app.include_router(selection.router, prefix="/api/selection", tags=["Selection"])
app.include_router(cookies.router, prefix="/api/cookies", tags=["Cookies"])
