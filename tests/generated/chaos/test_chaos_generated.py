import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_simulate_latency_spike_failure_and_recovery():
    """
    Test: Simulate latency spike failure for tenant_demo, verify degraded response,
    then recover and verify healthy state.
    """
    tenant_id = "tenant_demo"
    failure_type = "latency_spike"

    # 1. Trigger failure
    failure_response = client.post(
        "/simulate/failure",
        json={"tenant_id": tenant_id, "failure_type": failure_type}
    )
    assert failure_response.status_code == 200
    failure_data = failure_response.json()
    assert "status" in failure_data

    # 2. Assert degraded state: /ready should now fail (as per failure simulation)
    ready_response = client.get("/ready")
    assert ready_response.status_code != 200, "Expected /ready to fail after latency_spike failure"

    # 3. Trigger recovery
    recovery_response = client.post("/simulate/recovery")
    assert recovery_response.status_code == 200
    recovery_data = recovery_response.json()
    assert "status" in recovery_data

    # 4. Assert healthy state restored
    ready_response_after = client.get("/ready")
    assert ready_response_after.status_code == 200


def test_simulate_error_spike_failure_and_recovery():
    """
    Test: Simulate error spike failure for tenant_acme, verify degraded response,
    then recover and verify healthy state.
    """
    tenant_id = "tenant_acme"
    failure_type = "error_spike"

    # 1. Trigger failure
    failure_response = client.post(
        "/simulate/failure",
        json={"tenant_id": tenant_id, "failure_type": failure_type}
    )
    assert failure_response.status_code == 200
    failure_data = failure_response.json()
    assert "status" in failure_data

    # 2. Assert degraded state: /ready should fail (as per failure simulation)
    ready_response = client.get("/ready")
    assert ready_response.status_code != 200, "Expected /ready to fail after error_spike failure"

    # 3. Trigger recovery
    recovery_response = client.post("/simulate/recovery")
    assert recovery_response.status_code == 200
    recovery_data = recovery_response.json()
    assert "status" in recovery_data

    # 4. Assert healthy state restored
    ready_response_after = client.get("/ready")
    assert ready_response_after.status_code == 200


def test_simulate_readiness_failure_and_recovery():
    """
    Test: Simulate readiness failure for tenant_demo, verify /ready returns non-200,
    then recover and verify /ready returns 200 again.
    """
    tenant_id = "tenant_demo"
    failure_type = "readiness_failure"

    # 1. Trigger failure
    failure_response = client.post(
        "/simulate/failure",
        json={"tenant_id": tenant_id, "failure_type": failure_type}
    )
    assert failure_response.status_code == 200
    failure_data = failure_response.json()
    assert "status" in failure_data

    # 2. Assert degraded state: /ready should fail
    ready_response = client.get("/ready")
    assert ready_response.status_code != 200, "Expected /ready to fail after readiness_failure"

    # 3. Trigger recovery
    recovery_response = client.post("/simulate/recovery")
    assert recovery_response.status_code == 200
    recovery_data = recovery_response.json()
    assert "status" in recovery_data

    # 4. Assert healthy state restored
    ready_response_after = client.get("/ready")
    assert ready_response_after.status_code == 200


def test_failure_request_validation_error():
    """
    Test: Ensure /simulate/failure rejects invalid request bodies.
    """
    # Missing required fields
    response = client.post("/simulate/failure", json={"tenant_id": "tenant_demo"})
    assert response.status_code == 422

    # Invalid failure_type
    response = client.post(
        "/simulate/failure",
        json={"tenant_id": "tenant_demo", "failure_type": "invalid_type"}
    )
    assert response.status_code == 422
