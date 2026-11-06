# Architecture Analysis Task Packet Prompt

Use this prompt to ask the coding agent to explore the repository structure, map dependencies, and report architectural findings back to the chat.

---

```markdown
Create an Agent Task Relay task packet for local architectural exploration:

### Investigation Goal:
[Describe what you want to understand: e.g. database schema migrations, caching layer, authentication pipeline]

### Deliverables Expected:
1. Summary of current design patterns and call flows.
2. Inventory of dependencies and external integrations.
3. List of technical debt items, bottleneck risks, or modernization opportunities.
4. Non-invasive: No application source modifications permitted.

### Task Packet Requirements:
- Filename: `inbox/TASK-arch-<topic>.md`
- Acceptance criteria: Clear Markdown report saved as agent response.

Submit to my private bridge repository or provide the text for manual commit.
```
