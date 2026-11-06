# Changelog

All notable changes to **Agent Task Relay** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-07

### Added
- Complete refactoring from RelayCrate preview into **Agent Task Relay** (`agent-task-relay`).
- Standard Python package architecture with `pyproject.toml` (PEP 621), `src/agent_task_relay/` layout, and `agent-task-relay` / `atr` CLI entrypoints.
- Provider-agnostic runner architecture (`BaseRunner`) with support tiers:
  - Verified: `mock` (deterministic zero-token handshake) and `custom` (fixed executable allowlist, argument arrays, isolated env).
  - Experimental: `agy` (Google Antigravity CLI), `claude` (Anthropic Claude Code CLI), `gemini` (Google Gemini CLI).
  - Contract: `codex` (OpenAI Codex CLI), `opencode` (OpenCode CLI), `local` (Local agent harness).
- Cryptographic content-bound task approvals binding approval to the exact SHA-256 hash of task files, invalidating approval if the task is modified.
- Full task lifecycle state machine (`pending` → `approved` → `claimed` → `running` → `completed` / `failed` / `needs-review`), plus `rejected`, `cancelled`, and `interrupted` handling.
- Background service lifecycle management (`start`, `stop`, `restart`, `status`, `logs`) with atomic process locks, PID tracking, and stale lock reclamation.
- OS autostart service definitions for Windows Task Scheduler (`schtasks`), Linux systemd user units, and macOS launchd.
- Comprehensive secret redaction engine for reports (GitHub tokens, OpenAI/Anthropic keys, AWS credentials, Slack tokens, private keys, passwords).
- Official Agent Skills specification compliance (`skills/agent-task-relay/SKILL.md`).
- Multi-provider chat-side prompt library (11 ready-to-copy prompts) and coding-agent prompt library (8 prompts).
- Complete documentation suite (Architecture, Getting Started, Configuration, Providers, Scheduling, Troubleshooting, and Turkish Guide).
- Multi-OS GitHub Actions CI workflow (Ubuntu, Windows) on Python 3.10, 3.11, 3.12, 3.13.
- Comprehensive test suite (45 unit and integration tests passing on Windows).

### Changed
- Decoupled core relay engine from proprietary models or specific chat APIs.
- Renamed all RelayCrate identifiers to Agent Task Relay.
- Replaced monolithic script with modular protocol, transport, runner, and service subpackages.

## [0.1.0] - 2026-11-06
- Initial RelayCrate v0.1.0 preview release.
