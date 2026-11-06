# First Hello-World Task (End-to-End Pipeline Validation)

Use this prompt to have your chat assistant create the initial mock handshake task.

---

```markdown
Create an initial handshake task packet to test the complete Agent Task Relay pipeline.

Requirements:
1. Target filename: `inbox/TASK-hello-<today's-date>.md`.
2. Objective: Confirm end-to-end task handoff through Git without altering application source code.
3. Scope: Strictly zero modifications to application files. The coding agent should only report receipt and verify workspace connectivity.
4. Acceptance criteria:
   - Coding agent receives task packet.
   - Status transitions to `completed`.
   - Result report is placed in `outbox/`.

If you have write access to my private bridge repository, commit this file now. Otherwise, output the complete Markdown file for me to commit manually.
```
