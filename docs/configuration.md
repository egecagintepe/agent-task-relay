# Configuration Reference

Agent Task Relay stores local configuration in `.agent-task-relay/config.json` inside your project workspace.

## Configuration Schema

```json
{
  "version": 1,
  "bridge": "C:/Dev/my-agent-bridge",
  "workspace": "C:/Dev/my-app",
  "runner": "mock",
  "poll_seconds": 60,
  "timeout_seconds": 3600,
  "approval_mode": "manual",
  "custom_runner": {
    "command": ["python", "scripts/agent.py", "--task", "{task_file}", "--dir", "{workspace}"],
    "allowed_executables": ["python", "node", "pytest"],
    "env_vars": {}
  }
}
```

### Options Description

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `version` | integer | `1` | Configuration schema version. |
| `bridge` | string | *(required)* | Absolute path to the private Git bridge clone. |
| `workspace` | string | *(required)* | Absolute path to the software development codebase. |
| `runner` | string | `"mock"` | Selected runner adapter (`mock`, `agy`, `claude`, `gemini`, `codex`, `opencode`, `local`, `custom`). |
| `poll_seconds` | integer | `60` | Polling interval for background watcher (minimum 5s). |
| `timeout_seconds`| integer | `3600` | Maximum time in seconds allowed for a single runner task (default 60m). |
| `approval_mode` | string | `"manual"` | Task approval policy (`"manual"` or `"auto"`). |
| `custom_runner` | object | `null` | Settings for the generic custom command runner. |

## Approved Tasks (`.agent-task-relay/approved.json`)

When you run `agent-task-relay approve TASK-001 --yes`, the relay records the task approval and its cryptographic SHA-256 hash:

```json
{
  "version": 1,
  "tasks": {
    "TASK-001": {
      "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
      "approved_at": "2026-11-07T00:15:00Z"
    }
  }
}
```

If anyone modifies `TASK-001.md` after approval, the hash check fails and the task is safely skipped.
