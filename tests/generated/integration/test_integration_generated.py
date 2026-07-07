import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_ready_version_consistency(client):
    """
    Integration test: Verify that /health, /ready, and /version return consistent
    service identity and status information.
    """
    health_resp = client.get("/health")
    ready_resp = client.get("/ready")
    version_resp = client.get("/version")

    assert health_resp.status_code == 200
    assert ready_resp.status_code == 200
    assert version_resp.status_code == 200

    health_data = health_resp.json()
    ready_data = ready_resp.json()
    version_data = version_resp.json()

    # All endpoints should indicate service is operational
    assert health_data.get("status") == "ok"
    assert ready_data.get("status") == "ok"

    # Version data must match expected service identity
    assert version_data["service"] == "testrms"
    assert version_data["version"] == "rel_local_001"
    assert version_data["environment"] == "qa"

    # Health and ready should include version info
    assert health_data.get("version") == version_data["version"]
    assert ready_data.get("version") == version_data["version"]


def test_tenant_config_consistency(client):
    """
    Integration test: Verify that tenant config endpoints return consistent
    data for known tenants and properly handle unknown tenants.
    """
    # Test known tenant: tenant_demo
    demo_config_resp = client.get("/tenant/tenant_demo/config")
    assert demo_config_resp.status_code == 200
    demo_config = demo_config_resp.json()

    # Verify expected structure and values
    assert demo_config["policy_profile"] == "standard"
    assert demo_config["slo_profile"] == "standard"
    assert demo_config["feature_flags"]["new_checkout"] is False
    assert demo_config["feature_flags"]["agent_write_actions"] is False

    # Test known tenant: tenant_acme
    acme_config_resp = client.get("/tenant/tenant_acme/config")
    assert acme_config_resp.status_code == 200
    acme_config = acme_config_resp.json()

    assert acme_config["policy_profile"] == "strict"
    assert acme_config["slo_profile"] == "gold"
    assert acme_config["feature_flags"]["new_checkout"] is True

    # Test unknown tenant returns 404
    unknown_resp = client.get("/tenant/unknown_tenant/config")
    assert unknown_resp.status_code == 404


def test_failure_simulation_and_recovery(client):
    """
    Integration test: Verify that failure simulation endpoints correctly
    change behavior and that recovery restores normal operation.
    """
    # Reset to clean state first
    client.post("/simulate/recovery")

    # Verify initial healthy state
    health_resp = client.get("/health")
    assert health_resp.status_code == 200

    # Simulate error spike
    failure_req = {"tenant_id": "tenant_demo", "failure_type": "error_spike"}
    failure_resp = client.post("/simulate/failure", json=failure_req)
    assert failure_resp.status_code == 200

    # Now verify that error spike is active: /tenant config should return 503
    tenant_resp = client.get("/tenant/tenant_demo/config")
    assert tenant_resp.status_code == 503
    assert tenant_resp.json()["detail"] == "simulated error spike"

    # Verify /health and /ready still return 200 (excluded from error spike)
    health_resp = client.get("/health")
    assert health_resp.status_code == 200

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200

    # Simulate recovery
    recovery_resp = client.post("/simulate/recovery")
    assert recovery_resp.status_code == 200

    # Verify normal operation restored
    tenant_resp = client.get("/tenant/tenant_demo/config")
    assert tenant_resp.status_code == 200


def test_metrics_endpoint_with_failure_simulation(client):
    """
    Integration test: Verify that metrics endpoint reflects state changes
    during failure simulation and that metrics are properly rendered.
    """
    # Reset to clean state
    client.post("/simulate/recovery")

    # Get initial metrics
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics_text = metrics_resp.text

    # Verify Prometheus format headers and basic structure
    assert "text/plain" in metrics_resp.headers["content-type"]
    assert "testrms_requests_total" in metrics_text
    assert "testrms_errors_total" in metrics_text

    # Simulate error spike
    failure_req = {"tenant_id": "tenant_demo", "failure_type": "error_spike"}
    client.post("/simulate/failure", json=failure_req)

    # Trigger some requests that should increment error counters
    client.get("/tenant/tenant_demo/config")  # This will return 503

    # Get metrics again
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics_text = metrics_resp.text

    # Verify error metrics are present and updated
    assert "testrms_errors_total" in metrics_text

    # Simulate recovery
    client.post("/simulate/recovery")

    # Verify metrics endpoint still works after recovery
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert "testrms_requests_total" in metrics_resp.text


def test_latency_spike_simulation(client):
    """
    Integration test: Verify that latency spike simulation increases
    response time for non-metrics endpoints and that recovery restores
    normal timing.
    """
    # Reset to clean state
    client.post("/simulate/recovery")

    # Measure baseline latency
    import time
    start = time.perf_counter()
    client.get("/health")
    baseline_duration = time.perf_counter() - start

    # Simulate latency spike
    failure_req = {"tenant_id": "tenant_demo", "failure_type": "latency_spike"}
    client.post("/simulate/failure", json=failure_req)

    # Verify latency spike: /health should take >1s
    start = time.perf_counter()
    client.get("/health")
    spike_duration = time.perf_counter() - start

    # Assert significant latency increase (allowing some tolerance)
    assert spike_duration > 1.0, f"Expected latency >1s during spike, got {spike_duration:.2f}s"

    # Verify metrics endpoint is NOT affected by latency spike
    start = time.perf_counter()
    client.get("/metrics")
    metrics_duration = time.perf_counter() - start

    # Metrics should remain fast (<0.5s)
    assert metrics_duration < 0.5, f"Metrics endpoint should not be affected by latency spike, got {metrics_duration:.2f}s"

    # Simulate recovery
    client.post("/simulate/recovery")

    # Verify latency returns to normal
    start = time.perf_counter()
    client.get("/health")
    recovery_duration = time.perf_counter() - start

    assert recovery_duration < 0.5, f"Expected latency <0.5s after recovery, got {recovery_duration:.2f}s"
