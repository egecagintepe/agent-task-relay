# Follow-Up or Correction Request Prompt

Use this prompt when a task result was incomplete, encountered errors, or needs course-correction.

---

```markdown
The previous task `TASK-<previous-id>` completed with caveats or failing tests:

### Issues Observed in Report:
[Paste excerpt from outbox result or describe what failed]

### Next Action:
1. Generate a **new unique task ID** (e.g., `TASK-<feature>-v2` or `TASK-<feature>-fix`). Never reuse a completed or failed task ID.
2. Incorporate lessons learned from the previous attempt.
3. Provide explicit guidance on how to avoid the previous error or roadblock.
4. Set tight acceptance criteria targeting the exact remaining defects.

Write the new task packet to `inbox/` or output the full Markdown block.
```
