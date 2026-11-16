# FastAPI entrypoint. Wires routers; nothing else lives here.
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.routers import analytics, documents, findings, playbooks, reviews, search

app = FastAPI(title="Clausebook API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened to the web/add-in origins in deploy config
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
app.include_router(reviews.router, prefix="/v1/reviews", tags=["reviews"])
app.include_router(findings.router, prefix="/v1/findings", tags=["findings"])
app.include_router(playbooks.router, prefix="/v1/playbooks", tags=["playbooks"])
app.include_router(search.router, prefix="/v1/search", tags=["search"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])


# Liveness check for the load balancer.
@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
