from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.database import init_db
from src.routers import health, dashboard, services, departments, reports, sync, debug
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FinOps Cloud Cost Optimizer...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Application shutdown complete")

app = FastAPI(
    title="FinOps Cloud Cost Optimizer",
    description="AWS cost visibility and optimization platform with AI-powered recommendations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(services.router, tags=["Services"])
app.include_router(departments.router, tags=["Departments"])
app.include_router(reports.router, tags=["Reports"])
app.include_router(sync.router, tags=["Sync"])
app.include_router(debug.router)

@app.get("/")
def root():
    return {
        "name": "FinOps Cloud Cost Optimizer",
        "version": "1.0.0",
        "description": "AWS cost visibility and optimization with AI-powered recommendations",
        "docs": "/docs",
        "health": "/health",
        "workflow": {
            "step1": "POST /api/sync/all - Fetch AWS Cost Explorer & CloudWatch metrics → stored in database",
            "step2": "POST /api/reports/generate - Generate AI optimization report → stored in database"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
