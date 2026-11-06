# Social Media Drafts (LinkedIn & X / Twitter)

## X / Twitter Thread

### Post 1 (Hook):
Your AI chat plans. Your coding agent builds.

I just released Agent Task Relay — a Git-backed bridge that connects conversational AI chats (ChatGPT, Claude) to local coding agents without copy-pasting or cloud API fees.

Thread 🧵👇

### Post 2 (The Problem):
We all plan features in ChatGPT or Claude, but execution requires manually copying instructions to a local coding agent (Antigravity, Claude Code, etc.) and pasting results back.

Most multi-agent frameworks require expensive orchestration APIs or heavy Docker stacks.

### Post 3 (The Git Solution):
Agent Task Relay uses a private Git repository as an asynchronous task queue:
📁 inbox/ → Chat commits TASK-001.md
📁 state/ → Local watcher claims and tracks SHA-256 state
📁 outbox/ → Coding agent runs tests and pushes report

### Post 4 (Key Guarantees):
🔒 Zero relay LLM API keys needed (pure Python stdlib + Git)
🛡️ Content-bound SHA-256 approvals prevent post-approval tampering
⚡ First test is a deterministic mock handshake (zero tokens)
💻 Background service with Windows Task Scheduler / systemd autostart

### Post 5 (CTA):
Check it out on GitHub:
👉 https://github.com/egecagintepe/agent-task-relay

Free for personal & internal use under PolyForm Internal Use 1.0.0.

---

## LinkedIn Post

**Stop copy-pasting between your AI chat and coding agents.**

Planning software architecture in ChatGPT or Claude is fast and intuitive. But getting those instructions to your local coding agent (such as Antigravity or Claude Code) and reviewing results usually means endless copy-pasting.

I built **Agent Task Relay** to solve this using a simple, durable medium: Git.

**How it works:**
1. Your AI chat designs a task and commits it to a private Git repository (`inbox/TASK-xxx.md`).
2. A lightweight background service detects it, verifies approval (cryptographically bound to SHA-256), and claims it.
3. Your local coding agent executes changes and runs test suites inside your workspace.
4. A structured, secret-redacted report is pushed to `outbox/` for review.

**Key Design Decisions:**
- **Zero Relay API Cost:** No OpenAI or Anthropic API keys required for the relay itself.
- **Durable Audit Trail:** Every handoff, state transition, and result is preserved in Git.
- **Provider Agnostic:** Compatible with ChatGPT, Claude, Gemini, Antigravity, and custom agent harnesses.

Repository: https://github.com/egecagintepe/agent-task-relay
#AI #SoftwareEngineering #Automation #Python #Git #Developers
