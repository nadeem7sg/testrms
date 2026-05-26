import os
from copy import deepcopy
from typing import Any


SERVICE_NAME = "testrms"


TENANT_CONFIGS: dict[str, dict[str, Any]] = {
    "tenant_demo": {
        "policy_profile": "standard",
        "slo_profile": "standard",
        "feature_flags": {
            "new_checkout": False,
            "agent_write_actions": False,
        },
    },
    "tenant_acme": {
        "policy_profile": "strict",
        "slo_profile": "gold",
        "feature_flags": {
            "new_checkout": True,
            "agent_write_actions": False,
        },
    },
}


def get_release_id() -> str:
    return os.getenv("RELEASE_ID", "rel_local_001")


def get_commit_sha() -> str:
    return os.getenv("COMMIT_SHA", "local")


def get_environment() -> str:
    return os.getenv("ENVIRONMENT", "qa")


def get_version_payload() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "version": get_release_id(),
        "commit_sha": get_commit_sha(),
        "environment": get_environment(),
    }


def get_tenant_config(tenant_id: str) -> dict[str, Any] | None:
    tenant_config = TENANT_CONFIGS.get(tenant_id)
    if tenant_config is None:
        return None

    payload = deepcopy(tenant_config)
    payload["tenant_id"] = tenant_id
    payload["release_id"] = get_release_id()
    return payload
