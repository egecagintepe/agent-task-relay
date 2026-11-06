# Coding Agent Runners & Support Matrix

Agent Task Relay decouples task transport from coding agent execution. A variety of runners are supported across three tiers:

## Runner Support Matrix

| Runner | Identifier | Tier | Requirements | Default Execution Mode |
| --- | --- | --- | --- | --- |
| **Mock Runner** | `mock` | **Verified** | Standard library only | Deterministic handshake, zero tokens |
| **Custom Command** | `custom` | **Verified** | Configured binary allowlist | Non-shell isolated process execution |
| **Google Antigravity** | `agy` | **Experimental** | `agy` CLI in PATH + interactive login | `agy -p <prompt> --output-format json` |
| **Claude Code** | `claude` | **Experimental** | `claude` CLI in PATH + Anthropic auth | `claude -p <prompt>` |
| **Google Gemini CLI** | `gemini` | **Experimental** | `gemini` CLI in PATH + Google auth | `gemini code --prompt <prompt>` |
| **OpenAI Codex CLI** | `codex` | **Contract** | Documented contract harness | `codex exec --task-file <file>` |
| **OpenCode** | `opencode` | **Contract** | OpenCode CLI in PATH | `opencode run --instruction-file <file>` |
| **Local Agent Harness** | `local` | **Contract** | Agent wrapper CLI (e.g. Ollama harness) | Custom agent wrapper with tools & fs |

> **Important Distinction:** A raw local language model (such as a bare `ollama` model endpoint) is **not** a coding agent. A coding agent requires an agent harness capable of reading files, modifying code, and using permitted tools.

## Configuring a Runner

Switch the active runner using the `config` command:

```bash
# Use Antigravity CLI
agent-task-relay config --runner agy --approval manual

# Use Claude Code CLI
agent-task-relay config --runner claude --approval manual

# Use Custom Command Runner
agent-task-relay config --runner custom
```

### Custom Runner Configuration

In `.agent-task-relay/config.json`:

```json
{
  "runner": "custom",
  "custom_runner": {
    "command": ["python", "scripts/agent_worker.py", "--task", "{task_file}", "--dir", "{workspace}"],
    "allowed_executables": ["python", "node", "pytest"]
  }
}
```
