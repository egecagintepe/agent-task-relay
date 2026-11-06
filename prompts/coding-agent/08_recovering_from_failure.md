# Coding Agent: Recovering from a Failed Execution

Instructions for diagnosing and recovering after a runner failure.

---

```markdown
A task packet failed with status `failed`.

Diagnostic Checklist:
1. Inspect the local log:
   ```bash
   agent-task-relay logs --task-id TASK-<failed-id>
   ```
2. Identify the failure category:
   - **Syntax or Test Failure:** Code was written but unit tests failed.
   - **Timeout Expired:** The task was too broad or a process hung.
   - **Dependency Missing:** A required CLI, binary, or package was not installed.
   - **Runner Crash:** Agent process encountered an unhandled exception.
3. Clean the workspace state:
   - Run tests to see current failures.
   - Revert incomplete or broken changes if necessary.
4. Prepare a revised task packet with a new ID (`TASK-<name>-retry`) addressing the root cause.
```
