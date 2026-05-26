from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_tenant_config() -> None:
    response = client.get("/tenant/tenant_demo/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant_demo"
    assert payload["policy_profile"] == "standard"
    assert payload["slo_profile"] == "standard"
    assert payload["feature_flags"]["agent_write_actions"] is False


def test_protected_tenant_config() -> None:
    response = client.get("/tenant/tenant_acme/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant_acme"
    assert payload["policy_profile"] == "strict"
    assert payload["slo_profile"] == "gold"
    assert payload["feature_flags"]["new_checkout"] is True


def test_unknown_tenant_returns_404() -> None:
    response = client.get("/tenant/missing/config")

    assert response.status_code == 404
