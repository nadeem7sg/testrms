# testrms

`testrms` is the first AqR/Sherpa pilot workload. It is intentionally small, deployable, tenant-aware, and observable so AqR can exercise the full release promotion flow against a real repository.

## Endpoints

- `GET /health` returns Kubernetes liveness status.
- `GET /ready` returns rollout readiness status.
- `GET /version` returns service, release, commit, and environment metadata.
- `GET /tenant/{tenant_id}/config` returns tenant-aware runtime config.
- `GET /metrics` exposes Prometheus metrics.
- `POST /simulate/failure` enables a rollback test failure mode.
- `POST /simulate/recovery` clears the simulated failure.

## Tenant Showcase Scenarios

This repository now models five tenant scenarios for AqR demos:

| Tenant | Segment | Routing | Gate profile | Demo purpose |
| --- | --- | --- | --- | --- |
| `tenant_demo` | default | shared | standard | fast happy-path release |
| `tenant_startup` | startup | shared | fast lane | low-friction canary with latency checks |
| `tenant_acme` | enterprise | dedicated | protected enterprise | protected-tenant approvals and rollback drill |
| `tenant_finance` | regulated | dedicated | regulated finance | compliance evidence and audit reconstruction |
| `tenant_sovereign` | sovereign | dedicated | sovereign strict | data residency, runtime drift, and permanent evidence |

Pilot hostnames follow the AqR tenant access plane convention:

```text
http://tenant-demo.89.169.121.117.nip.io/
http://tenant-startup.89.169.121.117.nip.io/
http://tenant-acme.89.169.121.117.nip.io/
http://tenant-finance.89.169.121.117.nip.io/
http://tenant-sovereign.89.169.121.117.nip.io/
```

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

## AqR Onboarding

AqR should register this repository as:

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

Expected north-star milestone:

```text
AqR North Star Pilot - tenant-aware testrms release governance
```

Protected tenants are `tenant_acme`, `tenant_finance`, and `tenant_sovereign`; AqR should require the configured approval roles and rollback evidence before promotion.
