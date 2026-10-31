"""FastAPI application entry point."""
from __future__ import annotations
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.projects import router as projects_router
from app.infrastructure.database import Base, engine
from app.infrastructure import project_models  # noqa: F401
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(title="RobotLab Web API", version="0.2.0",
    description="Calculation engines and project API for RobotLab Web.", lifespan=lifespan)
app.include_router(projects_router)
@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0"}
