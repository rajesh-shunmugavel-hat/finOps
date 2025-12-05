from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import dashboard, services, reports, departments

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinOps Cloud Cost Optimization API",
    description="AI-powered AWS cost analysis and optimization recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(services.router)
app.include_router(reports.router)
app.include_router(departments.router)

@app.get("/")
def root():
    return {
        "message": "FinOps API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
