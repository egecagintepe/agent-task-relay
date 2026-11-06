# Agent Task Relay Protocol v1

The Agent Task Relay protocol uses a private Git repository as an asynchronous, durable, reviewable task queue between AI chat assistants and local coding agents.

## Repository Layout

A private bridge repository must have the following structure:

```text
private-agent-bridge/
├── inbox/
│   ├── .gitkeep
│   └── TASK-0001.md
├── state/
│   ├── .gitkeep
│   └── TASK-0001.json
├── outbox/
│   ├── .gitkeep
│   └── TASK-0001.result.md
└── archive/
    └── .gitkeep
```

The user's code repository remains strictly separate from the bridge.

## Task Packets (`inbox/TASK-<ID>.md`)

- **Filename format:** `TASK-[A-Za-z0-9][A-Za-z0-9._-]{0,79}.md` (maximum 85 characters).
- **Encoding:** UTF-8.
- **Maximum file size:** 200,000 bytes (200 KB).
- **Forbidden:** Path separators (`/`, `\`), null bytes (`\0`), traversal sequences (`..`), symlinks.

### Recommended Structure

```markdown
# TASK-0001: Implement Health Check Endpoint

## Objective
Add a lightweight `/healthz` endpoint returning HTTP 200 with JSON `{"status": "ok"}`.

## Context
FastAPI service in `src/api/main.py`.

## Scope
- Allowed: Add router endpoint and test case.
- Non-goals: Do not touch database models or authentication dependencies.

## Acceptance criteria
- [ ] GET `/healthz` returns status code 200
- [ ] Response payload is `{"status": "ok"}`
- [ ] Unit tests in `tests/test_health.py` pass cleanly

## Safety and approval
Do not deploy, modify credentials, or access external services.
```

## State Machine (`state/TASK-<ID>.json`)

The state machine enforces valid state transitions and rejects illegal leaps:

```text
               ┌─────────────┐
               │   PENDING   │
               └──────┬──────┘
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ APPROVED │ │ REJECTED │ │CANCELLED │
   └─────┬────┘ └──────────┘ └──────────┘
         ▼
   ┌──────────┐
   │ CLAIMED  │
   └─────┬────┘
         ▼
   ┌──────────┐
   │ RUNNING  │
   └─────┬────┘
   ┌─────┼─────────────┐
   ▼     ▼             ▼
┌─────┐┌────────┐┌─────────────┐
│DONE ││ FAILED ││NEEDS-REVIEW │
└─────┘└────────┘└─────────────┘
```

### State Fields

```json
{
  "task_id": "TASK-0001",
  "status": "completed",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "claimed_at": "2026-11-07T00:00:00Z",
  "host": "workstation-1",
  "attempt": 1,
  "runner": "mock",
  "started_at": "2026-11-07T00:00:01Z",
  "finished_at": "2026-11-07T00:00:02Z",
  "duration_seconds": 1.2,
  "changed_files": []
}
```

## Result Reports (`outbox/TASK-<ID>.result.md`)

When execution completes, the relay publishes a Markdown report to `outbox/`:
- Status header and duration.
- Exact task SHA-256 for auditability.
- Changed files list.
- Sanitized and secret-redacted agent response.
- Clear disclaimer that results must be reviewed independently.
