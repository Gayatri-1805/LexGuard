"""
FastAPI application for legal-domain LLM hallucination detection.

Wires KB layer (postgres_kb.py, vector_kb.py) and detection pipeline (Person A)
into an HTTP API for developers (Person B) and analytics dashboard (Person C).

Routes:
  GET /health — uptime check
  POST /check — hallucination detection (calls detection-engine/pipeline.py)
  GET /analytics/summary — aggregate stats
  GET /analytics/checks — paginated recent checks
  GET /analytics/flagged — flagged claims for review

CORS enabled for local dev (TODO: restrict before production).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from api.routes.check import router as check_router
from api.routes.analytics import router as analytics_router

app = FastAPI(
    title="Legal Hallucination Detector API",
    description="Detects and scores LLM hallucinations in legal domain using multi-stage verification pipeline",
    version="0.1.0",
)

# CORS middleware (TODO: restrict origins before production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(check_router, prefix="/api", tags=["Detection"])
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])


@app.get("/health")
async def health():
    """Health check endpoint for uptime monitoring and dashboard verification."""
    return {"status": "ok"}
