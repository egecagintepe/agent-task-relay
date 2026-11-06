# Security Policy

## Supported Versions

Only the latest release of Agent Task Relay receives active security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2.0 | :x:                |

## Threat Model and Trust Boundaries

Agent Task Relay is built on the explicit security posture that **all incoming Markdown task packets are untrusted data**, even when retrieved from a private Git repository.

### Core Guarantees:
- **No Command Construction via String Concatenation:** The relay executes runner commands using strict argument vectors (`list[str]`) and explicitly sets `shell=False`.
- **Content-Bound Approvals:** Approvals are cryptographically tied to the SHA-256 hash of task files. If a task is modified after human approval, the approval is immediately invalidated and the task will not run.
- **Directory Traversal Protection:** All task filenames are checked against the regex `^TASK-[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.md$`. Path separators (`/`, `\`), parent navigation (`..`), and null bytes (`\0`) are rejected.
- **Symlink Defense:** Task files and bridge folders cannot be symlinks.
- **Secret Redaction:** Outbox result reports are scrubbed for API keys, tokens (GitHub, OpenAI, Anthropic, AWS, Slack), private keys, and passwords before commit and push.
- **Local Logs Stay Local:** Unredacted execution logs remain strictly on the local machine under `.agent-task-relay/logs/` and are excluded from Git via `.gitignore`.
- **Separation of Workspace and Bridge:** Bridge repositories and workspace code directories must be separate directories. Neither may be nested inside the other.
- **No Silent Re-execution:** A task that was previously claimed but whose process crashed or terminated is never silently re-run.

### Non-Negotiable Human Escalation:
No task file may grant itself permission to:
- Deploy software to staging or production environments.
- Execute destructive operations (dropping databases, deleting storage buckets).
- Exfiltrate, rotate, or modify secrets or credentials.
- Modify repository collaborator permissions or branch protection rules.

## Reporting a Vulnerability

If you discover a security vulnerability in Agent Task Relay, please do **NOT** open a public issue.

Instead, please send a responsible disclosure report to:
`egecagintepe@gmail.com`

Please include:
1. Description of the vulnerability and attack vector.
2. Steps to reproduce or proof-of-concept payload.
3. Potential impact and suggested mitigations.

We will acknowledge receipt within 48 hours and work with you on a coordinated fix and release.
