# Show HN: Agent Task Relay – Bridge AI chats to local coding agents via Git

**Title:** Show HN: Agent Task Relay – Bridge AI chats to local coding agents via Git

**Link:** https://github.com/egecagintepe/agent-task-relay

Hi HN,

I built Agent Task Relay to connect conversational AI interfaces (ChatGPT, Claude, Gemini) with local autonomous coding agents without manual copy-pasting or cloud API dependencies.

### Motivation
Chat models are great for planning software architecture, clarifying constraints, and reviewing test outcomes. Local coding agents (such as Google Antigravity, Claude Code, or local harnesses) are great at editing code and running test suites.

Bridging them typically involves copy-pasting Markdown prompts, or paying for third-party multi-agent cloud wrappers.

### How it works
The system uses a private Git repository as an asynchronous task queue:
- `inbox/`: Chat writes structured task packets (`TASK-*.md`).
- `state/`: Local background service claims tasks, binds approvals to content SHA-256 hashes, and tracks state.
- `outbox/`: The runner records duration, test results, changed files, and sanitized outputs.

### Architecture principles
- **Zero Relay API Cost:** The local daemon relies on Python stdlib and Git. It exposes no listening network port by default.
- **Content-Bound Approvals:** If a task file is modified after approval, the relay invalidates the approval to prevent unauthorized modifications.
- **Provider Agnostic:** Supports mock, Antigravity, Claude Code, Gemini CLI, custom command allowlists, and local agent harnesses.
- **License:** PolyForm Internal Use License 1.0.0 (source-available, free for personal and internal business use).

Source and documentation: https://github.com/egecagintepe/agent-task-relay

Feedback and suggestions are welcome!
