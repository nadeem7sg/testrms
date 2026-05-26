from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, Info, generate_latest

from app.config import SERVICE_NAME, get_commit_sha, get_environment, get_release_id


REQUESTS_TOTAL = Counter(
    "testrms_requests_total",
    "Total HTTP requests served by testrms.",
    ["method", "path", "status"],
)

REQUEST_LATENCY_SECONDS = Histogram(
    "testrms_request_latency_seconds",
    "HTTP request latency for testrms.",
    ["method", "path"],
)

ERRORS_TOTAL = Counter(
    "testrms_errors_total",
    "Total HTTP error responses served by testrms.",
    ["path", "status"],
)

TENANT_REQUESTS_TOTAL = Counter(
    "testrms_tenant_requests_total",
    "Total tenant-scoped requests served by testrms.",
    ["tenant_id", "path"],
)

ACTIVE_RELEASE_INFO = Info(
    "testrms_active_release",
    "Active release metadata for testrms.",
)


def refresh_release_info() -> None:
    ACTIVE_RELEASE_INFO.info(
        {
            "service": SERVICE_NAME,
            "release_id": get_release_id(),
            "commit_sha": get_commit_sha(),
            "environment": get_environment(),
        }
    )


def render_metrics() -> tuple[bytes, str]:
    refresh_release_info()
    return generate_latest(), CONTENT_TYPE_LATEST
