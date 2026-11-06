# Result Inspection & Review Prompt

Copy and paste this prompt when asking your chat assistant to review the output of a completed task packet.

---

```markdown
Please review the result report for my task in the private bridge repository:

Task ID: `TASK-<task-id>`

1. Read `outbox/TASK-<task-id>.result.md` and check `state/TASK-<task-id>.json`.
2. Verify:
   - What was the execution status (`completed`, `failed`, or `needs-review`)?
   - What files were modified? Are these within the allowed scope?
   - Did the acceptance tests pass? What evidence did the agent provide?
   - Are there any warnings, tool denials, or blockers noted?
3. Assess whether the outcome satisfies our original objective.
4. If satisfied, summarize what was achieved. If further iteration is needed, propose the next bounded follow-up task packet.
```
