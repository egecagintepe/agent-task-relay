# Agent Task Relay v0.2.0 Release Notes

**Tagline:** Bridge any AI chat to any coding agent through Git.  
**License:** PolyForm Internal Use License 1.0.0 (Source-Available)

## Highlights

- **Chat-First Development Orchestration:** Use standard conversational AI (ChatGPT, Claude, Gemini) to plan tasks while a local coding agent executes and tests code.
- **Zero Relay LLM API Cost:** Operates locally using Python standard library primitives and Git. No third-party LLM API keys needed for the relay engine.
- **Durable Task Transport:** A private Git repository serves as an auditable queue with `inbox/`, `state/`, and `outbox/` folders.
- **Content-Bound Approvals:** Approvals are cryptographically tied to the SHA-256 hash of task files, immediately blocking execution if a task is tampered with post-approval.
- **Provider-Agnostic Runner System:**
  - Verified Live: `mock` (zero-token handshake) and `custom` (sandboxed arguments & allowlists).
  - Experimental: `agy` (Google Antigravity), `claude` (Anthropic Claude Code), `gemini` (Google Gemini CLI).
  - Contract: `codex` (OpenAI Codex), `opencode` (OpenCode), `local` (Local agent harness).
- **Background Daemon & OS Autostart:** Built-in background service management with process locking, stale PID recovery, and autostart script generation for Windows Task Scheduler, systemd, and launchd.
- **Secret Redaction Safeguards:** Defense-in-depth sanitization of tokens, credentials, private keys, and passwords before reports are committed to Git.

## Quick Installation

```bash
# Install directly from GitHub:
pip install git+https://github.com/egecagintepe/agent-task-relay.git
```

## Documentation
- [Quickstart Guide](https://github.com/egecagintepe/agent-task-relay#readme)
- [System Architecture](https://github.com/egecagintepe/agent-task-relay/blob/main/docs/architecture.md)
- [ChatGPT Setup Guide](https://github.com/egecagintepe/agent-task-relay#chatgpt-quickstart)
