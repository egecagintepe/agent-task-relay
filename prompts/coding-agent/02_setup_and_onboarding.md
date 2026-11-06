# Coding Agent: Setup and Onboarding

Instruct your coding agent to set up Agent Task Relay with safe paths.

---

```markdown
Read `.agents/skills/agent-task-relay/SKILL.md` (or the repository documentation).

Please execute the Agent Task Relay onboarding workflow:

1. Confirm the absolute path to this project workspace: `<WORKSPACE_ABSOLUTE_PATH>`
2. Confirm the separate absolute path to my private Git bridge repository: `<BRIDGE_ABSOLUTE_PATH>`
3. Verify that the bridge repository is a valid Git clone with a private remote.
4. Run:
   ```bash
   agent-task-relay init --workspace <WORKSPACE_PATH> --bridge <BRIDGE_PATH> --runner mock
   ```
5. Run `agent-task-relay doctor` and show the diagnostic output.
6. Run `agent-task-relay ping` followed by `agent-task-relay once`.
7. Confirm that `outbox/TASK-ping-*.result.md` was created with a successful mock handshake.

Do NOT configure a live AI runner or auto-approval mode without my explicit subsequent consent.
```
