import importlib
from fastapi.testclient import TestClient


def test_app_boots_and_responds():
    mod = importlib.import_module("app.main")
    app = getattr(mod, "app")
    client = TestClient(app)
    checked = 0
    for route in app.routes:
        methods = getattr(route, "methods", set()) or set()
        path = getattr(route, "path", "")
        if "GET" in methods and "{" not in path and not path.startswith("/openapi"):
            resp = client.get(path)
            assert resp.status_code < 500, f"{path} -> {resp.status_code}"
            checked += 1
    assert checked > 0, "no GET routes were exercised"
