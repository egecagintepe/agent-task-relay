# GitHub Connection Validation

Use this prompt to test whether your chat assistant's GitHub connector is active and determine its permission level (read-only vs read-write).

---

```markdown
Please check your GitHub connection to my private task bridge repository: `<YOUR_GITHUB_USERNAME>/<YOUR_PRIVATE_BRIDGE_REPO>`

Verify the following:
1. Can you read the repository contents? List the top-level files and folders (specifically checking for `inbox/`, `state/`, and `outbox/`).
2. Do you have authorized **write permission** to create or commit files in this repository?
3. Report your exact access status clearly:
   - **Full Read/Write:** You can directly create task files under `inbox/`.
   - **Read-Only:** You can inspect reports in `outbox/`, but I will manually commit task packets into `inbox/`.
   - **No Access:** Explain how to connect the repository or confirm manual fallback mode.
```
