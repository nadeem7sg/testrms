import importlib, json, time, statistics
from pathlib import Path
from fastapi.testclient import TestClient

MODULE = "app.main"
ATTR = "app"
ITER = 30
P95_MS = 750.0


def test_performance_latency():
    mod = importlib.import_module(MODULE)
    app = getattr(mod, ATTR)
    client = TestClient(app)
    paths = [
        getattr(r, "path", "")
        for r in app.routes
        if "GET" in (getattr(r, "methods", set()) or set())
        and "{" not in getattr(r, "path", "")
        and not getattr(r, "path", "").startswith("/openapi")
    ]
    assert paths, "no GET routes to benchmark"
    for p in paths:
        client.get(p)  # warmup
    samples = []
    for _ in range(ITER):
        for p in paths:
            t0 = time.perf_counter()
            client.get(p)
            samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    p95 = samples[max(0, int(len(samples) * 0.95) - 1)]
    metrics = {
        "count": len(samples),
        "routes": len(paths),
        "iterations": ITER,
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(p95, 3),
        "mean_ms": round(statistics.mean(samples), 3),
        "max_ms": round(max(samples), 3),
    }
    Path(".qa_perf.json").write_text(json.dumps(metrics))
    assert p95 <= P95_MS, f"p95 {p95:.1f}ms exceeds budget {P95_MS}ms"
