from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import connect

from app.cv_api import router as cv_router
from app.ingestion_api import router as ingestion_router
from app.jobs_api import router as jobs_router
from app.config import settings
from app.source_registry import router as source_registry_router

app = FastAPI(title="JobScout AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(source_registry_router)
app.include_router(ingestion_router)
app.include_router(cv_router)
app.include_router(jobs_router)


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with connect(settings.database_url) as connection:
            connection.execute("SELECT 1")
        return {"status": "ok", "database": "ok"}
    except Exception:
        return {"status": "degraded", "database": "unavailable"}


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "JobScout AI API", "status": "ok"}
