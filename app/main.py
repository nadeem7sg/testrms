import asyncio
import time
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from app.config import get_tenant_config, get_version_payload
from app.metrics import (
    ERRORS_TOTAL,
    REQUEST_LATENCY_SECONDS,
    REQUESTS_TOTAL,
    TENANT_REQUESTS_TOTAL,
    render_metrics,
)


class FailureRequest(BaseModel):
    tenant_id: str
    failure_type: Literal["latency_spike", "error_spike", "readiness_failure"]


app = FastAPI(title="testrms", version="rel_local_001")
app.state.failure_mode = None
app.state.failure_tenant_id = None


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    start = time.perf_counter()
    path = request.url.path

    if app.state.failure_mode == "latency_spike" and not path.startswith("/metrics"):
        await asyncio.sleep(1.25)

    if app.state.failure_mode == "error_spike" and path not in {
        "/health",
        "/ready",
        "/metrics",
    }:
        response = Response(
            content='{"detail":"simulated error spike"}',
            status_code=503,
            media_type="application/json",
        )
    else:
        response = await call_next(request)

    elapsed = time.perf_counter() - start
    status = str(response.status_code)
    REQUESTS_TOTAL.labels(request.method, path, status).inc()
    REQUEST_LATENCY_SECONDS.labels(request.method, path).observe(elapsed)
    if response.status_code >= 500:
        ERRORS_TOTAL.labels(path, status).inc()

    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if app.state.failure_mode == "readiness_failure":
        raise HTTPException(status_code=503, detail="simulated readiness failure")
    return {"status": "ready"}


@app.get("/version")
def version() -> dict[str, str]:
    return get_version_payload()


@app.get("/tenant/{tenant_id}/config")
def tenant_config(tenant_id: str) -> dict:
    config = get_tenant_config(tenant_id)
    if config is None:
        raise HTTPException(status_code=404, detail="unknown tenant")

    TENANT_REQUESTS_TOTAL.labels(tenant_id, "/tenant/{tenant_id}/config").inc()
    return config


@app.get("/metrics")
def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@app.post("/simulate/failure")
def simulate_failure(request: FailureRequest) -> dict[str, str]:
    if get_tenant_config(request.tenant_id) is None:
        raise HTTPException(status_code=404, detail="unknown tenant")

    app.state.failure_mode = request.failure_type
    app.state.failure_tenant_id = request.tenant_id
    return {
        "status": "failure_simulation_enabled",
        "tenant_id": request.tenant_id,
        "failure_type": request.failure_type,
    }


@app.post("/simulate/recovery")
def simulate_recovery() -> dict[str, str]:
    app.state.failure_mode = None
    app.state.failure_tenant_id = None
    return {"status": "recovered"}
