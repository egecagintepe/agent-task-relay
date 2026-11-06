# Large Development Task (30–60 Minute Milestone)

Use this prompt when turning a major feature discussion into an executable, bounded milestone.

---

```markdown
Based on our discussion, formulate a single bounded, high-impact task packet for the coding agent.

Guidelines:
1. Target filename: `inbox/TASK-<feature>-<component>.md`.
2. Title: A concise, descriptive summary of the outcome.
3. Bounded Scope: Target 30 to 60 minutes of focused engineering work. Do not bundle unrelated chores.
4. Acceptance Criteria: Write 3–6 objectively verifiable checkboxes that can be validated with automated tests or code inspection.
5. Invariants: Explicitly state which existing public interfaces, APIs, or behaviors must NOT be broken.
6. Safety: Remind the agent not to rotate secrets, touch production databases, or trigger cloud deployments.

Create the file in my private bridge repository or provide the complete Markdown block for manual submission.
```
