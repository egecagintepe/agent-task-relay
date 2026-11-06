# Getting Started with Agent Task Relay

Welcome to Agent Task Relay. This guide walks you through setting up a complete end-to-end task bridge between your favorite AI chat assistant (ChatGPT, Claude, Gemini) and a local coding agent.

## The 5-Minute Setup Journey

Meet **Sam**, a developer who wants to use ChatGPT to design software features during the day, while having a local coding agent (such as Antigravity, Claude Code, or a custom agent) implement the code and run local tests.

Here is how Sam gets running in 5 minutes:

---

### Step 1: Create a Separate Private Git Repository

Agent Task Relay uses a dedicated, private Git repository as an asynchronous task queue.

1. Go to GitHub and click **New Repository**.
2. Name it `my-agent-bridge` (or any private name you prefer).
3. **Important:** Select **Private**.
4. Check **Add a README file**.
5. Clone it locally:
   ```bash
   git clone git@github.com:<YOUR_USERNAME>/my-agent-bridge.git C:/Dev/my-agent-bridge
   ```

> [!IMPORTANT]
> Your task bridge repository must remain strictly separate from your software project repository. Never commit real task packets or logs into a public repository.

---

### Step 2: Install Agent Task Relay

Install directly from the GitHub repository:

```bash
pip install git+https://github.com/egecagintepe/agent-task-relay.git
```

Or clone and install locally:
```bash
git clone https://github.com/egecagintepe/agent-task-relay.git
cd agent-task-relay
pip install .
```

Verify installation:
```bash
agent-task-relay --version
```

---

### Step 3: Initialize Your Workspace and Bridge

Open a terminal in your software development project (e.g. `C:/Dev/my-app`) and run:

```bash
agent-task-relay init --workspace C:/Dev/my-app --bridge C:/Dev/my-agent-bridge --runner mock
```

This command:
- Verifies that both directories exist and are properly isolated.
- Creates the bridge folders (`inbox/`, `state/`, `outbox/`, `archive/`).
- Generates `.agent-task-relay/config.json` inside your project.
- Adds `.agent-task-relay/` to your project's `.gitignore` to prevent secret leakage.
- Copies the portable Agent Skill to `.agents/skills/agent-task-relay/`.

---

### Step 4: Audit Readiness with Doctor

Run the diagnostic audit to verify Python, Git, workspace, and bridge health:

```bash
agent-task-relay doctor
```

You should see:
```text
=== Agent Task Relay Doctor ===
Version:      0.2.0
Python:       3.12.x
Git CLI:      OK
Bridge repo:  OK (C:/Dev/my-agent-bridge) - OK (Remote detected)
Workspace:    OK (C:/Dev/my-app)
Runner:       mock [verified] -> AVAILABLE
Approval:     manual
Service:      Service is stopped.
```

---

### Step 5: Execute the Deterministic Mock Handshake

Test the complete transport loop with zero LLM tokens and zero risk to code:

```bash
agent-task-relay ping
```

Output:
```text
Ping task queued and locally approved: TASK-ping-20261107...
Inbox file: C:/Dev/my-agent-bridge/inbox/TASK-ping-20261107....md
Run `agent-task-relay once` to process the handshake.
```

Now execute one cycle:
```bash
agent-task-relay once
```

Output:
```text
[INFO] Claimed TASK-ping-20261107.... Dispatching to runner: mock ...
[INFO] Published result for TASK-ping-20261107...: completed (0.05s)
```

Inspect `C:/Dev/my-agent-bridge/outbox/TASK-ping-*.result.md` to confirm the report was pushed back to GitHub!

---

### Step 6: Connect Your AI Chat Assistant

Now configure your AI chat assistant (ChatGPT, Claude, or Gemini):

1. Connect your private repository (`<YOUR_USERNAME>/my-agent-bridge`) in your chat assistant's GitHub connector if available.
2. Copy the priming prompt from [`prompts/chat/01_initial_configuration.md`](../prompts/chat/01_initial_configuration.md).
3. Ask the assistant to submit your first real task packet!

---

### Step 7: Configure a Live Coding-Agent Runner

When you are ready for real code generation, switch from `mock` to your preferred runner:

```bash
# Using Google Antigravity CLI
agent-task-relay config --runner agy --approval manual

# Using Anthropic Claude Code
agent-task-relay config --runner claude --approval manual
```

Start the background service to process approved tasks automatically:
```bash
agent-task-relay start
```
