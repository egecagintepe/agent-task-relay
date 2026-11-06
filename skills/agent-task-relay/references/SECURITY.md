# Security and Trust Model

Agent Task Relay enforces a defense-in-depth security model designed around the assumption that **remotely supplied Markdown tasks are untrusted input**.

## Core Threat Assumptions

1. **Remote Tasks Are Untrusted:** Even within a private Git repository, prompt injections, malicious commands, or malformed instructions may be present in task packets.
2. **Never Execute Arbitrary Shell Code:** The relay never uses `shell=True` or constructs commands by concatenating Markdown task text.
3. **Workspace Isolation:** The bridge repository and the code workspace must be separate directories. The relay verifies this separation on initialization and startup.
4. **Symlink Traversal Prevention:** Symlinks are strictly forbidden for inbox task files, bridge folders, and state files.
5. **Content-Bound Approvals:** Task approvals are cryptographically bound to the SHA-256 hash of the task file. If a task file is modified after being approved, the approval is invalidated immediately.
6. **No Silent Re-execution:** A task that was previously claimed but whose process crashed or terminated is never silently re-run. Silent re-runs can duplicate side effects or corrupt workspace state.
7. **Secret Redaction:** Reports published back to Git are automatically scanned and redacted for API keys, tokens, AWS credentials, Slack tokens, private keys, and passwords.
8. **Local Logs Stay Local:** Raw stdout and stderr from coding agents are saved to local `.agent-task-relay/logs/` (which is excluded from Git via `.gitignore`) and are never committed to the bridge.

## High-Risk Operations Require Human Authorization

No task file can authorize itself to:
- Deploy software to staging or production.
- Modify database schemas or execute data migrations without supervision.
- Read, write, or rotate credentials, SSH keys, or environment secrets.
- Modify access control rules or repository collaborator permissions.
- Make financial transactions or purchase resources.

If a task packet attempts to trigger these actions, the coding agent must stop and report that additional human approval is required.
