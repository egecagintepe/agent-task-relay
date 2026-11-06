# Reddit Community Post Draft (r/ChatGPT, r/LocalLLaMA, r/Python)

**Title:** I built a Git-backed relay that connects ChatGPT and Claude chats to local coding agents without copy-pasting or cloud API fees

Hey everyone,

Like many developers, I do my architectural planning and brainstorming in conversational AI chats (ChatGPT / Claude), but I want my local coding agent (like Antigravity, Claude Code, or a local harness) to actually edit code and run local tests in my workspace.

The problem: You end up copying prompts and pasting results back and forth constantly. Most multi-agent frameworks require either paying for third-party cloud orchestration APIs or running complex Redis/Docker stacks.

I built **Agent Task Relay** to solve this using something we all already have: Git.

### How it works:
1. You chat with your assistant. It writes a structured Markdown task packet to a private Git bridge repo (`inbox/TASK-001.md`).
2. A lightweight local Python watcher pulls the bridge every 60s, checks SHA-256 approval, and claims the task.
3. The local coding agent implements the task and runs tests.
4. The relay redacts secrets and commits a structured report to `outbox/TASK-001.result.md`.
5. You or your chat assistant inspect the report and decide on the next iteration.

### Key points:
- **Zero Relay Tokens:** The relay requires no OpenAI or Anthropic API keys. It runs on pure Python standard library and Git.
- **Reuse Your Existing Plans:** Use your existing ChatGPT Plus/Team or Claude subscription.
- **Safety:** Content-bound SHA-256 approvals prevent post-approval task tampering. Commands run without `shell=True`.
- **First Test is Free:** Built-in `agent-task-relay ping` runs a deterministic mock handshake with zero AI calls.

Repository: https://github.com/egecagintepe/agent-task-relay

Source-available under PolyForm Internal Use License 1.0.0. Would love feedback!
