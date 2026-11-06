# Coding Agent: Handling an Interrupted Task

Guidance for investigating and recovering from a crash or interrupted run.

---

```markdown
An existing task `TASK-<id>` is marked as `claimed` in `state/TASK-<id>.json`, but the runner process terminated unexpectedly or the system rebooted.

Recovery Procedure:
1. Do NOT re-execute `TASK-<id>`. The relay prevents silent re-execution because partial code changes may already exist in the workspace.
2. Check `git status` in the workspace to see which files were modified before the crash.
3. Check `.agent-task-relay/logs/TASK-<id>.log` to inspect the last logged output prior to interruption.
4. Assess whether to keep or revert the uncommitted changes in the workspace:
   - If clean or easily resumable: commit or stash changes.
   - If corrupted: `git checkout -- .` to restore the clean branch state.
5. Create a **new task packet with a new ID** (e.g. `TASK-<feature>-resume`) describing the current state and what remains to be completed.
```
