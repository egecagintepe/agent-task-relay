# Agent Task Relay: One-Pager & Demo Captions

## One-Paragraph Project Introduction

> **Agent Task Relay** is a free-to-use, source-available developer tool and Agent Skill that connects conversational AI chats (ChatGPT, Claude, Gemini) with local coding agents (Antigravity, Claude Code, custom CLI harnesses) through a private Git repository. It eliminates repetitive copy-pasting between chat and coding agents without requiring third-party cloud orchestration APIs, Docker stacks, or external databases. With cryptographic content-bound approvals, an explicit task lifecycle state machine, and automatic secret redaction, Agent Task Relay enables safe, auditable, and durable task handoffs for personal and internal software engineering workflows.

---

## Three Concise Product Demonstration Captions

### Caption 1: The Git Handoff
> *From chat to code via Git:* ChatGPT drafts a bounded feature specification and commits it to a private `inbox/TASK-001.md`. No copy-pasting or browser automation required.

### Caption 2: Deterministic Mock Handshake
> *Zero tokens, instant verification:* Run `agent-task-relay ping && agent-task-relay once` to verify task claiming, runner dispatch, and outbox report publishing with a deterministic local handshake.

### Caption 3: Auditable Outbox Report
> *Review code changes and test output:* The coding agent implements the feature, runs local tests, and pushes a structured Markdown report to `outbox/TASK-001.result.md` with secret redaction applied.
