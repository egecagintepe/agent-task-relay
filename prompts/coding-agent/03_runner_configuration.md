# Coding Agent: Runner Configuration

Instruct the coding agent to configure the designated CLI runner.

---

```markdown
I have authorized switching Agent Task Relay to a live coding-agent runner.

Target Runner: [Select: `agy` | `claude` | `gemini` | `codex` | `opencode` | `custom`]
Approval Mode: `manual` (Keep manual approval for safety)

Please execute:
1. Verify the selected runner executable is present in PATH:
   - For `agy`: `agy --version`
   - For `claude`: `claude --version`
   - For `gemini`: `gemini --version`
2. Update the relay configuration:
   ```bash
   agent-task-relay config --runner <RUNNER> --approval manual
   ```
3. Run `agent-task-relay doctor` to verify runner readiness.
4. Explain how incoming tasks will be manually reviewed and approved (`agent-task-relay approve <TASK_ID> --yes`).
```
