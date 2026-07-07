import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_full_journey(client):
    """
    End-to-end journey:
    1. Verify service health and readiness
    2. Check version info
    3. Fetch tenant configs for both demo and ACME tenants
    4. Simulate a failure (latency spike) and verify degraded behavior
    5. Simulate recovery and verify normal behavior restored
    6. Verify metrics reflect the journey
    7. Final health check to confirm stable state
    """

    # Step 1: Verify service health and readiness
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok"}

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json() == {"status": "ready"}

    # Step 2: Check version info
    version_resp = client.get("/version")
    assert version_resp.status_code == 200
    version_data = version_resp.json()
    assert version_data["service"] == "testrms"
    assert version_data["version"] == "rel_local_001"
    assert version_data["environment"] == "qa"

    # Step 3: Fetch tenant configs
    demo_config_resp = client.get("/tenant/tenant_demo/config")
    assert demo_config_resp.status_code == 200
    demo_config = demo_config_resp.json()
    assert demo_config["policy_profile"] == "standard"
    assert demo_config["slo_profile"] == "standard"
    assert demo_config["feature_flags"]["new_checkout"] is False

    acme_config_resp = client.get("/tenant/tenant_acme/config")
    assert acme_config_resp.status_code == 200
    acme_config = acme_config_resp.json()
    assert acme_config["policy_profile"] == "strict"
    assert acme_config["slo_profile"] == "gold"
    assert acme_config["feature_flags"]["new_checkout"] is True

    # Non-existent tenant should return 404
    nonexistent_resp = client.get("/tenant/nonexistent/config")
    assert nonexistent_resp.status_code == 404

    # Step 4: Simulate latency spike failure
    failure_payload = {
        "tenant_id": "tenant_demo",
        "failure_type": "latency_spike"
    }
    failure_resp = client.post("/simulate/failure", json=failure_payload)
    assert failure_resp.status_code == 200
    assert failure_resp.json() == {"message": "Failure mode set: latency_spike"}

    # Verify latency spike: request to /tenant/tenant_demo/config should be slow (>1s)
    import time
    start = time.perf_counter()
    latency_test_resp = client.get("/tenant/tenant_demo/config")
    elapsed = time.perf_counter() - start
    assert latency_test_resp.status_code == 200
    assert elapsed >= 1.0, f"Expected latency spike, but elapsed only {elapsed:.3f}s"

    # Verify metrics endpoint still works (excluded from latency spike)
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics_text = metrics_resp.text
    assert "testrms_requests_total" in metrics_text
    assert "testrms_request_latency_seconds" in metrics_text

    # Step 5: Simulate recovery
    recovery_resp = client.post("/simulate/recovery")
    assert recovery_resp.status_code == 200
    assert recovery_resp.json() == {"message": "Failure mode cleared"}

    # Verify normal behavior restored: request should be fast (<0.2s)
    start = time.perf_counter()
    normal_resp = client.get("/tenant/tenant_demo/config")
    elapsed = time.perf_counter() - start
    assert normal_resp.status_code == 200
    assert elapsed < 0.2, f"Expected normal latency, but took {elapsed:.3f}s"

    # Step 6: Final metrics check to verify request counts increased
    final_metrics_resp = client.get("/metrics")
    assert final_metrics_resp.status_code == 200
    final_metrics_text = final_metrics_resp.text
    # Ensure metrics contain expected counters and are non-zero
    assert "testrms_requests_total" in final_metrics_text
    assert "testrms_errors_total" in final_metrics_text
    assert "testrms_tenant_requests_total" in final_metrics_text

    # Step 7: Final health check to confirm stable state
    final_health_resp = client.get("/health")
    assert final_health_resp.status_code == 200
    assert final_health_resp.json() == {"status": "ok"}

    final_ready_resp = client.get("/ready")
    assert final_ready_resp.status_code == 200
    assert final_ready_resp.json() == {"status": "ready"}
