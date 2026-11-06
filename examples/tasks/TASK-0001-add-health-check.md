# TASK-0001: Implement Health Check Endpoint

## Objective
Implement an HTTP GET `/healthz` endpoint returning a JSON payload `{"status": "ok", "version": "1.0.0"}` with HTTP status code 200.

## Context
- Web API service implemented in FastAPI.
- Target file: `src/api/routes.py` and router registration in `src/api/main.py`.

## Scope
- Allowed: Add router function in `src/api/routes.py` and unit test in `tests/test_routes.py`.
- Non-goals: Do not touch database models, authentication dependencies, or deployment manifests.
- Invariants: Preserve all existing `/api/v1/*` routes unchanged.

## Implementation guidance
- Keep dependencies minimal; use standard FastAPI / Starlette JSON response.
- Follow existing PEP 8 code style and type annotations.

## Acceptance criteria
- [ ] GET `/healthz` returns HTTP status code 200
- [ ] Response body matches `{"status": "ok", "version": "1.0.0"}` exactly
- [ ] Unit test in `tests/test_routes.py` validates status code and JSON payload
- [ ] All existing automated tests in `pytest tests/` pass without regression

## Validation & testing
- Run `pytest tests/test_routes.py -v`
- Include test execution results in final report

## Safety and approval constraints
Do not deploy, modify secrets, or alter production configuration.
