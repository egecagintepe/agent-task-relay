# Provider Capability Matrix & Integration Guide

Agent Task Relay connects two distinct classes of AI tools: **Conversational Chat Assistants** (planning & review) and **Coding Agent Runners** (execution & test).

## 1. Chat Assistant Capabilities (Chat-Side)

Conversational chat assistants create tasks and review reports. Their capabilities depend on their platform integrations and connectors:

| Chat Provider | GitHub Read Access | GitHub Write Access | Scheduled Tasks | Status / Notes |
| --- | --- | --- | --- | --- |
| **ChatGPT (Plus/Team/Pro)** | Verified (via Connector) | Verified (via Connector) | Verified (Min 1-hour interval) | Primary onboarding example. Reads `outbox/`, writes `inbox/`. |
| **Claude (Anthropic Web/App)**| Verified (via Integrations)| Verified (via Integrations)| Unverified | Interactive chat mode works; scheduled reviews need client support. |
| **Google Gemini (Advanced)** | Verified (via Workspace/Ext)| Unverified | Unverified | Read-only or manual copy-paste fallback recommended. |
| **Any Custom Chat / Web UI** | Manual Fallback | Manual Fallback | N/A | Fully supported via Mode D (Manual Fallback). |

> [!NOTE]
> **Read-only vs. Read/Write:** If a chat assistant has only read-only access to your GitHub repository, it can inspect completed reports in `outbox/`, but cannot automatically write new tasks. In this case, use Mode D (Manual Fallback): the assistant generates the Markdown in chat, and you commit it to `inbox/`.

---

## 2. Coding Agent Runners (Execution-Side)

Coding agents run locally on your machine, read the task packet, write code in the project workspace, and run tests:

| Runner | ID | Support Tier | Invocation Command | Approval / Auth Verification |
| --- | --- | --- | --- | --- |
| **Mock Runner** | `mock` | **Verified** | Internal Python function | Zero-token handshake, no auth required |
| **Custom Command** | `custom` | **Verified** | Configured allowlist array | User-managed local executables |
| **Google Antigravity CLI** | `agy` | **Experimental** | `agy -p <prompt> --output-format json` | Requires interactive `agy` login on host |
| **Anthropic Claude Code** | `claude` | **Experimental** | `claude -p <prompt>` | Requires Anthropic authentication |
| **Google Gemini CLI** | `gemini` | **Experimental** | `gemini code --prompt <prompt>` | Requires Google Cloud/Gemini auth |
| **OpenAI Codex CLI** | `codex` | **Contract** | `codex exec --task-file <file>` | Documented integration contract |
| **OpenCode** | `opencode` | **Contract** | `opencode run --instruction-file <file>` | Documented integration contract |
| **Local Agent Harness** | `local` | **Contract** | Custom local agent wrapper | Requires agent harness with tools & fs |

### Support Tiers Defined

- **Verified:** Fully implemented and automated in unit and integration test suites.
- **Experimental:** Implemented against published CLI command specifications; requires local provider CLI installation and interactive login.
- **Contract:** Defined interface contract and command conventions; labeled for future or third-party harness integration.
