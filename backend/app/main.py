from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas import DecisionRequest
from app.services.decider import make_decision

app = FastAPI(
    title=settings.app_name,
    description="AI-powered decision evaluation and risk analysis.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/v1/decisions")
def create_decision(request: DecisionRequest):
    return make_decision(
        scenario=request.scenario,
        context=request.context,
    )


@app.post("/api/v1/decisions/preview")
def preview_decision(request: DecisionRequest):
    return make_decision(
        scenario=request.scenario,
        context=request.context,
    )
