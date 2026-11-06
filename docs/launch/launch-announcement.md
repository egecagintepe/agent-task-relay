# Launch Announcement: Agent Task Relay v0.2.0

We're excited to introduce **Agent Task Relay** — a lightweight, source-available developer tool and Agent Skill that connects conversational AI chats to local coding agents through Git.

## The Problem

Planning complex software features in conversational AI chats (like ChatGPT, Claude, or Gemini) is intuitive and productive. But handing those tasks off to local coding agents (like Antigravity, Claude Code, or terminal harnesses) usually requires repetitive manual copy-pasting:
1. Copying the prompt from chat.
2. Pasting it into a local CLI.
3. Waiting for the agent to finish.
4. Copying the diff, test results, or error logs back to the chat.

Existing multi-agent frameworks often demand expensive cloud orchestration APIs, complex Docker stacks, or centralized databases.

## The Solution: Git as an Asynchronous Task Queue

Agent Task Relay uses a dedicated, private Git repository as an auditable inbox and outbox:
- Your AI chat formats a structured task packet and commits it to `inbox/TASK-xxxx.md`.
- A lightweight local background service detects the task, verifies content integrity (SHA-256), claims it, and dispatches it to your configured coding-agent runner.
- The coding agent writes code and runs tests inside your workspace.
- The relay redacts secrets and commits a structured report to `outbox/TASK-xxxx.result.md`.
- Your chat assistant inspects the report and helps you plan the next step.

## Key Features

- **No Relay LLM API Required:** Operates 100% locally with Python stdlib and Git.
- **Reuse Existing Accounts:** Works with your existing ChatGPT/Claude subscriptions and your local CLI agent access.
- **Security-First:** Content-bound SHA-256 approvals, non-shell execution, and secret redaction.
- **Deterministic Mock Handshake:** Test the complete pipeline end-to-end with zero tokens.

Repository: https://github.com/egecagintepe/agent-task-relay
