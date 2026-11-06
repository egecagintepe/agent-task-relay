# Provider Capability Matrix & Integration Guide

Agent Task Relay connects two distinct classes of AI tools: **Conversational Chat Assistants** (planning & review) and **Coding Agent Runners** (execution & test).

## 1. Chat Assistant Capabilities (Chat-Side)

Conversational chat assistants create tasks and review reports. Their capabilities depend on the user's specific account tier, connector scopes, and platform permissions:

| Chat Provider | GitHub Read Access | GitHub Write Access | Scheduled Task Checks | Integration Status & Notes |
| --- | --- | --- | --- | --- |
| **ChatGPT (Plus/Team/Pro)** | Verified (with GitHub connector) | Account-Dependent (requires write scope) | Read-only verified (min 1-hour interval) | Primary onboarding example. Interactive write works if write permission is granted. Scheduled writes are **unverified/untested**. |
| **Claude (Anthropic Web/App)**| Verified (via GitHub integration)| Account-Dependent (integration scopes) | Unverified (not natively scheduled) | Interactive chat mode works; scheduled execution requires external scheduling. |
| **Google Gemini (Advanced)** | Account-Dependent (Extensions)| Unverified | Unverified | Read-only or manual copy-paste fallback (Mode D) recommended. |
| **Any Custom Chat / Web UI** | Manual Fallback | Manual Fallback | Manual / External | 100% compatible via Mode D (Manual Fallback). |

> [!IMPORTANT]
> **Read-only vs. Read/Write Reality:**
> - If your chat assistant's GitHub integration has only read access, it can read completed reports from `outbox/`, but cannot commit new tasks to `inbox/`. Use **Mode D (Manual Fallback)**: the assistant outputs the task Markdown in chat, and you commit it into `inbox/`.
> - **Scheduled Tasks Do Not Imply Autonomous Writing:** Successfully committing a task in a live, interactive chat session does **not** prove that a background scheduled task can write or refresh tokens unattended. Always verify connector permissions in your own environment.

---

## 2. Coding Agent Runners (Execution-Side)

Coding agents run locally on your machine, read the task packet, write code in the project workspace, and run tests:

| Runner | ID | Support Tier | Invocation Command | Approval / Auth Verification |
| --- | --- | --- | --- | --- |
| **Mock Runner** | `mock` | **Verified** | Internal Python function | Zero-token handshake, no auth required |
| **Custom Command** | `custom` | **Verified** | Configured allowlist array | User-managed local executables |
| **Google Antigravity CLI** | `agy` | **Experimental** | `agy -p <prompt> --output-format json` | Requires interactive `agy` login on host |
| **Anthropic Claude Code** | `claude` | **Experimental** | `claude -p <prompt>` | Requires Anthropic authentication |
| **Google Gemini CLI** | `gemini` | **Experimental** | `gemini -p <prompt>` | Requires Google Cloud/Gemini auth |
| **OpenAI Codex CLI** | `codex` | **Contract** | `codex exec <prompt>` | Documented integration contract |
| **OpenCode** | `opencode` | **Contract** | `opencode run <prompt>` | Documented integration contract |
| **Local Agent Harness** | `local` | **Contract** | Custom local agent wrapper | Requires agent harness with tools & fs |

### Support Tiers Defined

- **Verified:** Fully implemented and automated in unit and integration test suites.
- **Experimental:** Implemented against published CLI command specifications; requires local provider CLI installation and interactive login.
- **Contract:** Defined interface contract and command conventions; labeled for future or third-party harness integration.
