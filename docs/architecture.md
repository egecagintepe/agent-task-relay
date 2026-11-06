# System Architecture & Technical Specifications

Agent Task Relay connects conversational AI assistants to autonomous coding agents using a private Git repository as an asynchronous, transparent, and durable transport layer.

## Architectural Principles

1. **Clean Separation of Concerns:**
   - **Chat Assistant:** High-level planning, requirements refinement, architectural guidance, report review.
   - **Git Bridge:** Durable transport, distributed history, collaborator access control.
   - **Local Relay Service:** Validation, scheduling, locking, state management, secret redaction, audit logging.
   - **Coding Agent Runner:** Deep reasoning, code editing, tool execution, test verification.

2. **No Central Server or Cloud Daemon:**
   - The relay runs locally on the developer's machine.
   - It exposes no open TCP/HTTP listening ports by default, reducing attack surface.
   - Polling Git periodically (default 60 seconds) handles all ingress and egress.

3. **Explicit State Machine:**
   All tasks follow strict, non-reversible lifecycle state transitions:

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

## Transport Mechanics

1. **Pull Step:** `git pull --ff-only` on the bridge clone. If local modifications exist, the cycle aborts without executing tasks.
2. **Scan Step:** Scans `inbox/` for files matching `^TASK-[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.md$`. Symlinks and files exceeding 200 KB are skipped.
3. **Approval Check:**
   - Verifies whether the task ID is approved.
   - Verifies that the task file's current SHA-256 hash matches the SHA-256 hash recorded when approval was granted.
4. **Claim Step:**
   - Writes `state/TASK-<ID>.json` with status `claimed`, SHA-256, and host ID.
   - Commits and pushes the claim to the remote bridge BEFORE launching the runner.
   - **Crucial Rule:** If the claim push fails (due to push conflict or network error), the task is NOT executed.
5. **Execution Step:**
   - Invokes the configured runner (with explicit argument list, non-shell execution, and timeout).
   - Writes full unredacted stdout/stderr to `.agent-task-relay/logs/<ID>.log` locally.
6. **Publication Step:**
   - Generates `outbox/TASK-<ID>.result.md` with secret redaction applied.
   - Updates `state/TASK-<ID>.json` to `completed`, `failed`, or `needs-review`.
   - Commits and pushes both files to the remote bridge.
