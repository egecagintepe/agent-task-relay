# Safe Task Rejection Prompt

Use this prompt if the chat assistant authored a task that you decide not to execute.

---

```markdown
I have decided not to approve or execute task `TASK-<task-id>`.

Reasons for rejection:
[Specify reason: e.g. out of scope, requirements changed, architectural mismatch, risky approach]

Please acknowledge this decision. We will not run this task on the local coding agent.

Local operator command to record rejection:
```bash
agent-task-relay reject TASK-<task-id> --reason "[Reason for rejection]"
```

Let's discuss alternative approaches or redefine the requirements before creating any new task.
```
