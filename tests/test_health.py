from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_ready_and_version() -> None:
    recovery_response = client.post("/simulate/recovery")
    assert recovery_response.status_code == 200

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}

    ready_response = client.get("/ready")
    assert ready_response.status_code == 200
    assert ready_response.json() == {"status": "ready"}

    version_response = client.get("/version")
    assert version_response.status_code == 200
    assert version_response.json()["service"] == "testrms"


def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "testrms_requests_total" in response.text
    assert "testrms_request_latency_seconds" in response.text
    assert "testrms_active_release_info" in response.text


def test_failure_and_recovery_controls() -> None:
    failure_response = client.post(
        "/simulate/failure",
        json={"tenant_id": "tenant_acme", "failure_type": "readiness_failure"},
    )
    assert failure_response.status_code == 200

    ready_response = client.get("/ready")
    assert ready_response.status_code == 503

    recovery_response = client.post("/simulate/recovery")
    assert recovery_response.status_code == 200

    ready_after_recovery = client.get("/ready")
    assert ready_after_recovery.status_code == 200
