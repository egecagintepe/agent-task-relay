"""Ergonomic command-line interface for Agent Task Relay."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from agent_task_relay import __version__
from agent_task_relay.config import (
    RelayConfig,
    load_config,
    save_config,
    resolve_config_file,
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    record_task_approval,
)
from agent_task_relay.errors import (
    RelayError,
    ConfigurationError,
    SecurityError,
    TaskValidationError,
)
from agent_task_relay.protocol.models import StateRecord, TaskState
from agent_task_relay.protocol.report import generate_rejection_report
from agent_task_relay.protocol.task import (
    validate_task_id,
    validate_task_file_name,
    parse_task_file,
    TASK_FILE_PATTERN,
)
from agent_task_relay.runners.registry import get_runner, list_runners
from agent_task_relay.service.lifecycle import (
    start_service,
    stop_service,
    restart_service,
    get_service_status,
    generate_windows_task_command,
    generate_systemd_unit,
    generate_launchd_plist,
)
from agent_task_relay.service.watcher import TaskWatcher
from agent_task_relay.transport.bridge import Bridge
from agent_task_relay.transport.git import GitRepo


def init_cmd(args: argparse.Namespace) -> None:
    """Initialize a project workspace and separate private Git bridge."""
    workspace = Path(args.workspace or args.project or ".").expanduser().resolve()
    bridge_path = Path(args.bridge).expanduser().resolve()

    if not workspace.is_dir():
        raise ConfigurationError(f"Workspace directory does not exist: {workspace}")

    bridge = Bridge(bridge_path)
    bridge.validate_integrity(check_remote=False)

    if bridge_path == workspace or bridge_path in workspace.parents or workspace in bridge_path.parents:
        raise SecurityError(
            "Bridge directory and workspace directory must be strictly separate. "
            "Neither may be nested inside the other."
        )

    cfg_dir = workspace / CONFIG_DIR_NAME
    cfg_file = cfg_dir / CONFIG_FILE_NAME

    if cfg_file.exists() and not args.force:
        raise ConfigurationError(f"Configuration file already exists at {cfg_file}. Use --force to overwrite.")

    # Pull latest bridge updates
    bridge.pull()

    # Create bridge folders and .gitkeep files
    bridge.ensure_folders()

    # Copy skill into workspace from packaged bundle or repo fallback
    pkg_skill = Path(__file__).resolve().parent / "packaged_skill"
    repo_skill = Path(__file__).resolve().parents[2] / "skills" / "agent-task-relay"
    skill_src = pkg_skill if pkg_skill.is_dir() else (repo_skill if repo_skill.is_dir() else None)
    skill_dst = workspace / ".agents" / "skills" / "agent-task-relay"
    if skill_src and not skill_dst.exists():
        skill_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_src, skill_dst)
        print(f"Installed Agent Skill: {skill_dst}")

    # Write initial config
    cfg = RelayConfig(
        version=1,
        bridge=str(bridge_path),
        workspace=str(workspace),
        runner=args.runner,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.timeout_seconds,
        approval_mode="manual",
    )
    save_config(cfg_file, cfg)

    # Protect config directory from accidental Git commits in workspace
    gitignore = workspace / ".gitignore"
    existing_ignore = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    ignore_entry = f"\n# Local Agent Task Relay config, approvals, locks, logs\n{CONFIG_DIR_NAME}/\n"
    if f"{CONFIG_DIR_NAME}/" not in existing_ignore:
        with gitignore.open("a", encoding="utf-8") as f:
            f.write(ignore_entry)

    # Commit and push initial bridge structure
    try:
        bridge.git.add(["inbox/.gitkeep", "state/.gitkeep", "outbox/.gitkeep", "archive/.gitkeep"])
        if bridge.git.has_staged_changes():
            bridge.git.commit("chore: initialize Agent Task Relay bridge layout")
            bridge.git.push()
    except Exception as exc:
        print(f"[WARN] Initial bridge push notice: {exc}")

    print("\nInitialization complete:")
    print(f"  Workspace:      {workspace}")
    print(f"  Configuration:  {cfg_file}")
    print(f"  Private Bridge: {bridge_path}")
    print(f"  Runner:         {cfg.runner} ({cfg.approval_mode} approval)")
    print("\nNext steps:")
    print("  1. Run `agent-task-relay doctor` to verify environment.")
    print("  2. Run `agent-task-relay ping` to test deterministic mock handshake.")
    print("  3. Run `agent-task-relay once` to process the ping task.")


def doctor_cmd(args: argparse.Namespace) -> None:
    """Audit system dependencies, Git configuration, and runner readiness."""
    cfg_file, cfg = load_config(args.config)
    bridge = Bridge(Path(cfg.bridge))
    workspace = Path(cfg.workspace)

    print("=== Agent Task Relay Doctor ===")
    print(f"Version:      {__version__}")
    print(f"Python:       {sys.version.split()[0]} ({sys.executable})")
    print(f"Platform:     {sys.platform}")
    print(f"Config path:  {cfg_file}")

    # Check Git
    git_version = shutil.which("git")
    if git_version:
        try:
            ver = bridge.git.run_git("--version")
            print(f"Git CLI:      OK ({ver})")
        except Exception:
            print(f"Git CLI:      Found at {git_version} (error querying version)")
    else:
        print("Git CLI:      NOT FOUND in PATH")

    # Check Bridge
    try:
        bridge.validate_integrity(check_remote=False)
        has_rem = bridge.git.has_remote()
        rem_msg = "OK (Remote detected)" if has_rem else "WARNING (No remote detected)"
        print(f"Bridge repo:  OK ({bridge.root}) - {rem_msg}")
    except Exception as exc:
        print(f"Bridge repo:  ERROR: {exc}")

    # Check Workspace
    if workspace.is_dir():
        print(f"Workspace:    OK ({workspace})")
    else:
        print(f"Workspace:    MISSING ({workspace})")

    # Check Runner
    runner = get_runner(cfg.runner, cfg)
    avail, reason = runner.is_available()
    status_tag = "AVAILABLE" if avail else "UNAVAILABLE"
    print(f"Runner:       {runner.name} [{runner.tier}] -> {status_tag} ({reason})")

    # Check Approval Mode
    print(f"Approval:     {cfg.approval_mode}")

    # Check Service
    svc_status = get_service_status(cfg_file.parent)
    print(f"Service:      {svc_status['message']}")


def ping_cmd(args: argparse.Namespace) -> None:
    """Generate, queue, and approve a deterministic mock handshake task packet."""
    cfg_file, cfg = load_config(args.config)
    bridge = Bridge(Path(cfg.bridge))
    bridge.pull()

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    rand_hex = uuid.uuid4().hex[:6]
    task_id = f"TASK-ping-{timestamp}-{rand_hex}"

    task_file = bridge.inbox_dir / f"{task_id}.md"
    content = (
        f"# {task_id}: Agent Task Relay Handshake Test\n\n"
        "## Objective\n"
        "Verify the Git-backed transport pipeline: inbox → claim → runner → outbox report.\n\n"
        "## Context\n"
        "Deterministic mock ping initiated via `agent-task-relay ping`.\n\n"
        "## Scope\n"
        "Do not modify workspace application code or files.\n\n"
        "## Acceptance criteria\n"
        "- [x] Task packet placed in inbox\n"
        "- [x] State updated to claimed then completed\n"
        "- [x] Result report published in outbox\n\n"
        "## Safety and approval\n"
        "Handshake test only. Zero model tokens consumed.\n"
    )

    task_file.write_text(content, encoding="utf-8")
    rel_path = str(task_file.relative_to(bridge.root))
    bridge.git.add([rel_path])
    bridge.git.commit(f"task: {task_id} handshake ping")
    bridge.git.push()

    # Calculate content SHA-256 and approve
    packet = parse_task_file(task_file)
    record_task_approval(cfg_file.parent, task_id, packet.sha256)

    print(f"Ping task queued and locally approved: {task_id}")
    print(f"Inbox file: {task_file}")
    print("Run `agent-task-relay once` to process the handshake.")


def once_cmd(args: argparse.Namespace) -> None:
    """Execute a single polling and execution cycle."""
    cfg_file, cfg = load_config(args.config)
    watcher = TaskWatcher(cfg_file, cfg)
    with watcher.lock_context():
        processed = watcher.run_single_cycle()
        if not processed:
            print("No eligible tasks in inbox.")


def watch_cmd(args: argparse.Namespace) -> None:
    """Run the foreground polling loop."""
    cfg_file, cfg = load_config(args.config)
    watcher = TaskWatcher(cfg_file, cfg)
    watcher.watch()


def approve_cmd(args: argparse.Namespace) -> None:
    """Approve a specific pending task after human review."""
    task_id = validate_task_id(args.task_id)
    cfg_file, cfg = load_config(args.config)
    bridge = Bridge(Path(cfg.bridge))
    bridge.pull()

    task_file = bridge.inbox_dir / f"{task_id}.md"
    if not task_file.is_file():
        raise TaskValidationError(f"Task file not found in inbox: {task_file}")

    packet = parse_task_file(task_file)

    print(f"=== Task Review: {task_id} ===")
    print(f"Title:     {packet.title}")
    print(f"Size:      {packet.byte_size} bytes")
    print(f"SHA-256:   {packet.sha256}")
    print(f"File:      {task_file}")
    if packet.objective:
        print(f"\nObjective:\n{packet.objective}")
    if packet.scope:
        print(f"\nScope:\n{packet.scope}")
    if packet.acceptance_criteria:
        print("\nAcceptance criteria:")
        for item in packet.acceptance_criteria:
            print(f"  - {item}")
    print("================================")

    if not args.yes:
        raise SecurityError("Task approval requires confirmation with `--yes` after reviewing task contents.")

    record_task_approval(cfg_file.parent, task_id, packet.sha256)
    print(f"\nApproved task {task_id} locally (content SHA-256 bound).")
    print("The task is now eligible for execution on the next polling cycle.")


def reject_cmd(args: argparse.Namespace) -> None:
    """Explicitly reject a task packet and record the rejection in state and outbox."""
    task_id = validate_task_id(args.task_id)
    cfg_file, cfg = load_config(args.config)
    bridge = Bridge(Path(cfg.bridge))
    bridge.pull()

    task_file = bridge.inbox_dir / f"{task_id}.md"
    if not task_file.is_file():
        raise TaskValidationError(f"Task file not found in inbox: {task_file}")

    packet = parse_task_file(task_file)
    try:
        host = bridge.git.run_git("config", "user.name") or "operator"
    except Exception:
        host = "operator"

    reason = args.reason or "Task rejected by operator during manual review."
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    state_rec = StateRecord(
        task_id=task_id,
        status=TaskState.REJECTED.value,
        sha256=packet.sha256,
        claimed_at=now_iso,
        host=host,
        finished_at=now_iso,
        rejection_reason=reason,
    )

    report_content = generate_rejection_report(task_id, packet.sha256, reason, host)
    bridge.write_report(
        task_id=task_id,
        report_md=report_content,
        state_record=state_rec,
        commit_and_push=True,
        message=f"reject: {task_id} (rejected by operator)",
    )

    print(f"Task {task_id} rejected and published to outbox.")


def status_cmd(args: argparse.Namespace) -> None:
    """Display task status summary and service health."""
    cfg_file, cfg = load_config(args.config)
    bridge = Bridge(Path(cfg.bridge))
    bridge.pull()

    print("=== Agent Task Relay Status ===")
    svc = get_service_status(cfg_file.parent)
    print(f"Service: {svc['message']}")
    print(f"Runner:  {cfg.runner} ({cfg.approval_mode} approval)\n")

    tasks = bridge.list_inbox_tasks()
    if not tasks:
        print("No tasks in inbox.")
        return

    print(f"{'Task ID':<35} {'Status':<15} {'Runner':<10} {'Details'}")
    print("-" * 75)
    for t in tasks:
        state = bridge.get_state(t.task_id)
        if state:
            st = state.status
            rnr = state.runner
            dur = f"{state.duration_seconds}s" if state.duration_seconds else ""
            print(f"{t.task_id:<35} {st:<15} {rnr:<10} {dur}")
        else:
            print(f"{t.task_id:<35} {'pending':<15} {'-':<10} {'Awaiting approval / claim'}")


def start_cmd(args: argparse.Namespace) -> None:
    """Start the watcher background service."""
    cfg_file, _ = load_config(args.config)
    pid = start_service(cfg_file)
    print(f"Agent Task Relay service started in background (PID: {pid}).")


def stop_cmd(args: argparse.Namespace) -> None:
    """Stop the running background service."""
    cfg_file, _ = load_config(args.config)
    stopped = stop_service(cfg_file.parent)
    if stopped:
        print("Agent Task Relay service stopped.")
    else:
        print("No active service process found.")


def restart_cmd(args: argparse.Namespace) -> None:
    """Restart the background service."""
    cfg_file, _ = load_config(args.config)
    pid = restart_service(cfg_file)
    print(f"Agent Task Relay service restarted (PID: {pid}).")


def logs_cmd(args: argparse.Namespace) -> None:
    """Inspect local logs for a task or service."""
    cfg_file, _ = load_config(args.config)
    log_dir = cfg_file.parent / "logs"

    if args.task_id:
        task_id = validate_task_id(args.task_id)
        task_log = log_dir / f"{task_id}.log"
        if not task_log.is_file():
            print(f"No log found for task {task_id} at {task_log}")
            return
        print(f"=== Log for {task_id} ===")
        print(task_log.read_text(encoding="utf-8", errors="replace"))
    else:
        svc_out = log_dir / "service_stdout.log"
        svc_err = log_dir / "service_stderr.log"
        print("=== Service Logs ===")
        if svc_out.is_file():
            print("--- STDOUT (last 40 lines) ---")
            lines = svc_out.read_text(encoding="utf-8", errors="replace").splitlines()
            print("\n".join(lines[-40:]))
        if svc_err.is_file():
            print("--- STDERR (last 40 lines) ---")
            lines = svc_err.read_text(encoding="utf-8", errors="replace").splitlines()
            print("\n".join(lines[-40:]))


def config_cmd(args: argparse.Namespace) -> None:
    """View or update configuration options."""
    cfg_file, cfg = load_config(args.config)
    modified = False

    if args.runner:
        cfg.runner = args.runner
        modified = True
    if args.approval:
        if args.approval == "auto" and not args.acknowledge_risk:
            raise SecurityError("Enabling 'auto' approval mode requires `--acknowledge-risk` flag.")
        cfg.approval_mode = args.approval
        modified = True
    if args.poll_seconds:
        cfg.poll_seconds = int(args.poll_seconds)
        modified = True
    if args.timeout_seconds:
        cfg.timeout_seconds = int(args.timeout_seconds)
        modified = True

    if modified:
        save_config(cfg_file, cfg)
        print("Configuration updated successfully.")

    print(json.dumps(cfg.to_dict(), indent=2))


def service_install_cmd(args: argparse.Namespace) -> None:
    """Generate autostart service definitions for Windows, Linux, or macOS."""
    cfg_file, _ = load_config(args.config)
    target_os = args.os.lower() if args.os else sys.platform

    print(f"=== Service Autostart Definition ({target_os}) ===")
    if target_os == "win32" or target_os == "windows":
        cmd = generate_windows_task_command(cfg_file)
        print("Run this command in an Administrator PowerShell to register the scheduled task:\n")
        print(cmd)
    elif target_os == "linux":
        unit = generate_systemd_unit(cfg_file)
        print("Place this definition at ~/.config/systemd/user/agent-task-relay.service:\n")
        print(unit)
        print("Then run: systemctl --user enable --now agent-task-relay.service")
    elif target_os == "darwin" or target_os == "macos":
        plist = generate_launchd_plist(cfg_file)
        print("Place this definition at ~/Library/LaunchAgents/com.agent-task-relay.plist:\n")
        print(plist)
        print("Then run: launchctl load ~/Library/LaunchAgents/com.agent-task-relay.plist")
    else:
        print(f"Unsupported OS target: {target_os}")


# Helper method for TaskWatcher context manager in once_cmd
def _lock_context(self):
    from agent_task_relay.service.lock import acquire_process_lock
    return acquire_process_lock(self.config_dir)

TaskWatcher.lock_context = _lock_context


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent-task-relay",
        description="Agent Task Relay: Bridge any AI chat to any coding agent through Git.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", help="Path to config file (default: searches upwards for .agent-task-relay/config.json)")

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # init
    p_init = subparsers.add_parser("init", aliases=["setup"], help="Initialize workspace and private bridge")
    p_init.add_argument("--workspace", "--project", dest="workspace", help="Target code workspace directory")
    p_init.add_argument("--bridge", required=True, help="Private Git bridge directory")
    p_init.add_argument("--runner", choices=["mock", "agy", "claude", "gemini", "codex", "opencode", "local", "custom"], default="mock")
    p_init.add_argument("--poll-seconds", type=int, default=60, help="Polling interval in seconds")
    p_init.add_argument("--timeout-seconds", type=int, default=3600, help="Task execution timeout in seconds")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing configuration")
    p_init.set_defaults(func=init_cmd)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Audit environment and runner readiness")
    p_doctor.set_defaults(func=doctor_cmd)

    # ping
    p_ping = subparsers.add_parser("ping", help="Queue and approve a mock handshake task")
    p_ping.set_defaults(func=ping_cmd)

    # once
    p_once = subparsers.add_parser("once", help="Run a single polling and execution cycle")
    p_once.set_defaults(func=once_cmd)

    # watch
    p_watch = subparsers.add_parser("watch", help="Run foreground polling loop")
    p_watch.set_defaults(func=watch_cmd)

    # approve
    p_approve = subparsers.add_parser("approve", help="Review and approve a task packet")
    p_approve.add_argument("task_id", help="Task ID to approve (e.g. TASK-001)")
    p_approve.add_argument("--yes", action="store_true", help="Confirm task review and approval")
    p_approve.set_defaults(func=approve_cmd)

    # reject
    p_reject = subparsers.add_parser("reject", help="Reject a task packet with reason")
    p_reject.add_argument("task_id", help="Task ID to reject")
    p_reject.add_argument("--reason", help="Explanation for rejecting the task")
    p_reject.set_defaults(func=reject_cmd)

    # status
    p_status = subparsers.add_parser("status", help="Show task queue and service status")
    p_status.set_defaults(func=status_cmd)

    # start
    p_start = subparsers.add_parser("start", help="Start background watcher service")
    p_start.set_defaults(func=start_cmd)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop background watcher service")
    p_stop.set_defaults(func=stop_cmd)

    # restart
    p_restart = subparsers.add_parser("restart", help="Restart background service")
    p_restart.set_defaults(func=restart_cmd)

    # logs
    p_logs = subparsers.add_parser("logs", help="Inspect execution or service logs")
    p_logs.add_argument("--task-id", help="Task ID to view logs for")
    p_logs.set_defaults(func=logs_cmd)

    # config
    p_cfg = subparsers.add_parser("config", help="View or update configuration")
    p_cfg.add_argument("--runner", choices=["mock", "agy", "claude", "gemini", "codex", "opencode", "local", "custom"])
    p_cfg.add_argument("--approval", choices=["manual", "auto"])
    p_cfg.add_argument("--acknowledge-risk", action="store_true")
    p_cfg.add_argument("--poll-seconds", type=int)
    p_cfg.add_argument("--timeout-seconds", type=int)
    p_cfg.set_defaults(func=config_cmd)

    # service-install
    p_svc = subparsers.add_parser("service-install", help="Generate OS autostart service definitions")
    p_svc.add_argument("--os", choices=["windows", "linux", "macos"])
    p_svc.set_defaults(func=service_install_cmd)

    args = parser.parse_args()
    try:
        args.func(args)
    except RelayError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
