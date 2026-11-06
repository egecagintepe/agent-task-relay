# Troubleshooting & Diagnostics Guide

This guide provides recovery procedures for common operational and environment issues in Agent Task Relay.

## 1. Quick Diagnostic Check

Always start with the doctor command:
```bash
agent-task-relay doctor
```

Inspect local service or task logs:
```bash
# View service stdout and stderr
agent-task-relay logs

# View execution logs for a specific task
agent-task-relay logs --task-id TASK-001
```

---

## 2. Common Scenarios and Solutions

### Issue: "Skipped unapproved task TASK-xxx"
**Cause:** The relay is configured in `manual` approval mode (the recommended safe default), and this task has not yet been approved.
**Solution:**
Inspect the task:
```bash
agent-task-relay approve TASK-xxx
```
Review the objective, scope, and acceptance criteria. If satisfied, confirm with:
```bash
agent-task-relay approve TASK-xxx --yes
```

---

### Issue: "SECURITY ALERT: Task content was modified after approval!"
**Cause:** The task file in `inbox/` was modified after you approved it. The current SHA-256 hash does not match the recorded hash.
**Solution:**
This is an intentional security safeguard against post-approval tampering. Re-inspect the file to review the new changes:
```bash
agent-task-relay approve TASK-xxx --yes
```
This binds approval to the updated content hash.

---

### Issue: "Task was already claimed... Silently re-running claimed tasks is disabled"
**Cause:** The worker process crashed, was forcefully terminated, or the computer rebooted while executing a task. The relay deliberately refuses to re-execute claimed tasks to avoid duplicate code modifications.
**Solution:**
1. Check `git status` in your project workspace to inspect uncommitted changes.
2. Check `.agent-task-relay/logs/TASK-xxx.log` to see what happened before the crash.
3. If the changes are valid, commit or stash them.
4. To finish the remaining work, create a **new task packet with a new task ID** (e.g. `TASK-xxx-resume`). Never delete state files to force re-execution.

---

### Issue: "Watcher already running or active lock held at run.lock"
**Cause:** Another instance of `agent-task-relay` is currently running, or a previous process was killed without releasing the lock.
**Solution:**
The relay automatically cleans up stale locks if the recorded PID is dead. If the process is still alive:
```bash
# Check status
agent-task-relay status

# Stop background instance if running
agent-task-relay stop
```
If you verified no instance is running, manually remove `.agent-task-relay/run.lock`.

---

### Issue: Git Push Conflict or Network Failure
**Cause:** The bridge repository has divergent commits, or network connectivity was temporarily interrupted.
**Solution:**
1. `cd` into your private bridge clone (`C:/Dev/my-agent-bridge`).
2. Run `git status` and `git pull --ff-only`.
3. If there are merge conflicts, resolve them manually and run `git push`.
4. The relay will resume normal polling on its next cycle.

---

### Issue: Runner Soft-Denial ("needs-review")
**Cause:** The coding agent CLI (e.g., Antigravity or Claude Code) encountered a tool permission barrier (such as running shell commands or editing outside files) that was soft-denied.
**Solution:**
The task report will be marked as `needs-review`. Check the report in `outbox/` and your local logs to see what tool was requested. Grant minimal necessary local permissions interactively if appropriate.
