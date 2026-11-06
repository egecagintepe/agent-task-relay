# Chat Integration, Operations & Scheduling

Agent Task Relay enables chat-first development orchestration while keeping the relay engine completely provider-agnostic.

## Primary Use Case

A developer plans and reviews software development using an ordinary conversational AI interface (ChatGPT, Claude, Gemini) while a separate, specialized coding agent implements the code changes locally.

## The Four Operation Modes

### Mode A — Interactive Chat (Recommended Default)
1. The developer discusses a feature or bug in a normal chat window.
2. The assistant formats a structured task packet conforming to the relay schema.
3. If the chat has authorized GitHub write access to the user's private bridge repository, it commits the file directly to `inbox/TASK-xxxx.md`.
4. The local relay detects, claims, and executes the task via the configured coding agent.
5. The developer asks the assistant: *"Inspect the latest report in outbox and summarize the results."*
6. The assistant reviews the diffs and test results and proposes the next step.

### Mode B — Scheduled Chat Checks
- If the chat platform supports scheduled tasks (e.g. ChatGPT scheduled tasks) with verified GitHub read permissions, the assistant can periodically review completed reports.
- **Scheduling Realities:** Standard ChatGPT scheduled tasks cannot be scheduled more frequently than hourly.
- Scheduled tasks consume normal account usage allowances and do not guarantee instant response or write access.
- Local polling (60s default) is completely independent of chat-side scheduling.

### Mode C — Local Autonomous Execution
- When configured with `--approval auto --acknowledge-risk`, the local relay automatically claims and executes newly arrived approved tasks without waiting for manual command-line approval.
- This depends entirely on the local runner and permissions, not on the chat assistant.

### Mode D — Manual Fallback
- If the chat assistant has only read-only GitHub access or no GitHub connector at all, it outputs the complete Markdown task packet in the chat.
- The user saves the file into `inbox/` or uses the GitHub web UI to commit it.
- The rest of the workflow remains 100% functional.

## Cost & Token Honesty

- **Relay Overhead:** Zero LLM API calls required for the relay itself.
- **Chat Conversations:** Consume standard chat provider allowances/tokens.
- **Coding Agents:** Consume their own respective model allowances, credits, or subscriptions.
- **No Magic:** "No required chat API" means you don't need to purchase third-party orchestration API keys, but your chat and coding agents still use their respective provider services.
