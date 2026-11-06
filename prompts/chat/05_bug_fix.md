# Bug Fix Task Packet Prompt

Use this prompt to generate a focused bug-fix task from an error log, bug report, or failing test.

---

```markdown
I have identified a bug. Please convert this issue into an Agent Task Relay task packet:

### Bug Summary:
[Describe the bug, symptom, or unexpected behavior here]

### Error Trace / Logs:
[Paste error logs, stack trace, or terminal output here]

### Target Task Requirements:
1. Filename: `inbox/TASK-fix-<short-issue-name>.md`
2. Objective: Fix the root cause and add a regression test preventing future recurrence.
3. Scope: Narrow strictly to the affected module and test suite. Do not refactor unrelated code.
4. Validation: Specify the exact test command the agent must execute to prove the fix.
5. Format: Standard Agent Task Relay Markdown.

Submit the file to my private bridge repository or provide the full text for manual upload.
```
