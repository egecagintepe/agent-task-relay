# Scheduling & Automation Guide

A common source of confusion in AI workflows is the relationship between **chat-side scheduling** and **local service polling**. This guide clarifies their operational boundaries.

## Independent Clocks: Local Polling vs. Chat Scheduling

```text
┌────────────────────────────────────────────────────────┐
│                   Chat Provider Cloud                  │
│  (e.g., ChatGPT Scheduled Task, minimum interval 1hr)  │
└──────────────────────────┬─────────────────────────────┘
                           │ Reads outbox/ once per hour
                           ▼
              ┌──────────────────────────┐
              │   Private Git Bridge     │
              │  (github.com/user/bridge)│
              └────────────┬─────────────┘
                           ▲
                           │ Pulls & checks inbox/ every 60s
┌──────────────────────────┴─────────────────────────────┐
│                 Local Developer Machine                │
│             (Agent Task Relay Background Service)      │
└────────────────────────────────────────────────────────┘
```

- **Local Relay Service:** Runs on your local machine and polls Git every 60 seconds (or your configured `poll_seconds`). It consumes zero tokens and makes no LLM API calls.
- **Chat Assistant (ChatGPT):** Lives in the cloud. It does **not** wake up in real time because a Git commit was pushed.
- **ChatGPT Scheduled Tasks:** At the time of this release, standard ChatGPT scheduled tasks support a minimum recurrence interval of **one hour**. Scheduled tasks consume standard account usage allowances and message limits.

## Setting Up a ChatGPT Scheduled Check

If your ChatGPT account supports scheduled tasks and has write/read access to your private bridge repository via a GitHub connector, you can register an hourly reviewer:

### Suggested Prompt for Hourly ChatGPT Scheduled Task:

```markdown
Review the outbox in my private Agent Task Relay repository: `<YOUR_USERNAME>/<YOUR_BRIDGE_REPO>`.

Instructions:
1. Check `outbox/` for newly completed `TASK-*.result.md` reports alongside their matching `state/TASK-*.json` files.
2. Summarize only newly completed tasks:
   - What status was reported?
   - What files were modified?
   - Did all automated tests pass?
   - Were any blockers or permission barriers reported?
3. Do NOT automatically trigger a new task unless you have verified write permission and I previously authorized the next step.
4. If there are no new completed tasks, report "No newly completed tasks."
```

## Running the Local Relay as a Background Service

On your local machine, keep the relay running in the background without needing to leave a terminal window open:

### 1. Built-in Background Service
```bash
# Start in background
agent-task-relay start

# Check status
agent-task-relay status

# Stop service
agent-task-relay stop
```

### 2. Windows Task Scheduler Autostart
Generate the command to register the service to start automatically on Windows logon:
```bash
agent-task-relay service-install --os windows
```
Run the generated `schtasks` command in an Administrator PowerShell.

### 3. Linux systemd User Service
Generate the unit file definition:
```bash
agent-task-relay service-install --os linux
```
Save to `~/.config/systemd/user/agent-task-relay.service` and run:
```bash
systemctl --user enable --now agent-task-relay.service
```

### 4. macOS launchd Plist
Generate the launchd definition:
```bash
agent-task-relay service-install --os macos
```
Save to `~/Library/LaunchAgents/com.agent-task-relay.plist` and run:
```bash
launchctl load ~/Library/LaunchAgents/com.agent-task-relay.plist
```
