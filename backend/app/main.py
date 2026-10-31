"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="RobotLab Web API",
    version="0.1.0",
    description="Calculation engines and project API for RobotLab Web.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
