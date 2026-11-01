"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.battery import router as battery_router
from app.api.components import router as components_router
from app.api.diagnostics import router as diagnostics_router
from app.api.electrical import router as electrical_router
from app.api.mechanical import router as mechanical_router
from app.api.motorization import router as motorization_router
from app.api.projects import router as projects_router
from app.domain.units import InvalidInputError
from app.infrastructure import component_models, project_models  # noqa: F401
from app.infrastructure.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="RobotLab Web API",
    version="0.3.0",
    description="Calculation engines and project API for RobotLab Web.",
    lifespan=lifespan,
)
app.include_router(projects_router)
app.include_router(components_router)
app.include_router(battery_router)
app.include_router(electrical_router)
app.include_router(diagnostics_router)
app.include_router(mechanical_router)
app.include_router(motorization_router)


@app.exception_handler(InvalidInputError)
async def invalid_input_handler(_: Request, exc: InvalidInputError) -> JSONResponse:
    """Physically impossible inputs are client errors, never a 500."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.3.0"}
