# testrms

`testrms` is the first Sherpa pilot workload. It is intentionally small, deployable, tenant-aware, and observable so Sherpa can exercise the full release promotion flow against a real repository.

## Endpoints

- `GET /health` returns Kubernetes liveness status.
- `GET /ready` returns rollout readiness status.
- `GET /version` returns service, release, commit, and environment metadata.
- `GET /tenant/{tenant_id}/config` returns tenant-aware runtime config.
- `GET /metrics` exposes Prometheus metrics.
- `POST /simulate/failure` enables a rollback test failure mode.
- `POST /simulate/recovery` clears the simulated failure.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Test

```bash
pytest
```

## Build

```bash
docker build -t testrms:local .
docker run --rm -p 8080:8080 testrms:local
```

## Sherpa Onboarding

Sherpa should register this repository as:

```json
{
  "provider": "github",
  "repository": "nadeem7sg/testrms",
  "default_branch": "main",
  "release_branch_pattern": "release/*",
  "webhook_events": ["push", "pull_request", "workflow_run"]
}
```

The workload metadata lives in:

- `sherpa/release.yaml`
- `sherpa/tenants.yaml`
- `sherpa/eval-pack.yaml`
- `sherpa/policy-context.yaml`

Expected pilot milestone:

```text
Sherpa Pilot Workload v1 - testrms
```

The protected tenant is `tenant_acme`; Sherpa should require release manager, SRE, and security approval before promotion.
