from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db

# Import models so Base.metadata knows every table, and the tenancy
# listener is registered before any session is used.
import app.models  # noqa: F401
import app.core.tenancy  # noqa: F401

from app.api.routes import router as api_router
from app.services.compliance import ComplianceBlockedError
from app.services.seed import seed_default_tenants
from app.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    await seed_default_tenants()
    start_scheduler()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    yield
    await stop_scheduler()
    print("👋 Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Omni-Channel CRM & Marketing Automation Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — the app frontend plus embedded public forms (handled per-route)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-SubAccount-ID"],
)

@app.exception_handler(ComplianceBlockedError)
async def compliance_blocked_handler(request: Request, exc: ComplianceBlockedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

# Routes
app.include_router(api_router, prefix=settings.API_PREFIX)

# Real-time pipeline sync (mounted at root: ws://host/ws/pipeline)
from app.api.routes.pipeline_ws import router as pipeline_ws_router
app.include_router(pipeline_ws_router)

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
