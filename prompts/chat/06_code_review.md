# Code Review Task Packet Prompt

Use this prompt to dispatch a comprehensive static code review and security audit task to the local coding agent.

---

```markdown
Generate an Agent Task Relay task packet requesting a thorough local code review:

### Target Review Area:
[Specify path, module, or recent branch changes to review]

### Review Focus:
1. Logic errors, concurrency hazards, and edge cases.
2. Adherence to project architecture and typing conventions.
3. Security considerations (injection risks, unsanitized inputs, credential handling).
4. Test coverage adequacy.

### Task Packet Requirements:
- Filename: `inbox/TASK-review-<component>.md`
- Scope: Read-only analysis. The coding agent should NOT modify application files unless generating test fixtures.
- Output: A structured review report categorizing findings by severity (Critical, Warning, Suggestion).

Submit to my private bridge repository or output the complete Markdown.
```
