"""Background service lifecycle management (start, stop, restart, status) and OS integrations."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from agent_task_relay.errors import RelayError
from agent_task_relay.service.lock import is_pid_alive

PID_FILE_NAME = "service.pid"


def get_pid_file(config_dir: Path) -> Path:
    return config_dir / PID_FILE_NAME


def read_service_pid(config_dir: Path) -> int | None:
    pid_file = get_pid_file(config_dir)
    if not pid_file.is_file():
        return None
    try:
        pid_str = pid_file.read_text(encoding="utf-8").strip()
        pid = int(pid_str)
        return pid if pid > 0 else None
    except Exception:
        return None


def write_service_pid(config_dir: Path, pid: int) -> None:
    pid_file = get_pid_file(config_dir)
    pid_file.write_text(f"{pid}\n", encoding="utf-8")


def remove_service_pid(config_dir: Path) -> None:
    pid_file = get_pid_file(config_dir)
    if pid_file.exists():
        try:
            pid_file.unlink()
        except OSError:
            pass


def get_service_status(config_dir: Path) -> dict[str, Any]:
    """Inspect background service state."""
    pid = read_service_pid(config_dir)
    lock_file = config_dir / "run.lock"
    lock_held = lock_file.exists()

    if pid is not None:
        alive = is_pid_alive(pid)
        if alive:
            return {
                "running": True,
                "pid": pid,
                "lock_held": lock_held,
                "message": f"Service is active in background (PID: {pid}).",
            }
        else:
            # Dead process left stale PID file
            return {
                "running": False,
                "pid": pid,
                "lock_held": lock_held,
                "message": f"Service is NOT running (stale PID file found: {pid}).",
            }

    return {
        "running": False,
        "pid": None,
        "lock_held": lock_held,
        "message": "Service is stopped.",
    }


def start_service(config_file: Path) -> int:
    """Launch the watcher as an independent background service."""
    config_dir = config_file.parent
    status = get_service_status(config_dir)
    if status["running"]:
        raise RelayError(f"Service is already running with PID {status['pid']}.")

    # Spawn detached background process
    cmd = [
        sys.executable,
        "-m", "agent_task_relay.cli",
        "--config", str(config_file.resolve()),
        "watch",
    ]

    log_dir = config_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    service_out = (log_dir / "service_stdout.log").open("a", encoding="utf-8")
    service_err = (log_dir / "service_stderr.log").open("a", encoding="utf-8")

    creationflags = 0
    if sys.platform == "win32":
        # DETACHED_PROCESS = 0x00000008, CREATE_NEW_PROCESS_GROUP = 0x00000200
        creationflags = 0x00000008 | 0x00000200

    proc = subprocess.Popen(
        cmd,
        cwd=str(config_dir.parent),
        stdout=service_out,
        stderr=service_err,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=(sys.platform != "win32"),
    )

    # Verify process didn't instantly exit
    time.sleep(0.3)
    if proc.poll() is not None:
        raise RelayError(f"Background service process exited immediately with code {proc.returncode}. Check logs.")

    write_service_pid(config_dir, proc.pid)
    return proc.pid


def stop_service(config_dir: Path) -> bool:
    """Stop the running background service."""
    pid = read_service_pid(config_dir)
    if pid is None or not is_pid_alive(pid):
        remove_service_pid(config_dir)
        return False

    if sys.platform == "win32":
        # Graceful termination via taskkill
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T"], check=False, capture_output=True)
        except OSError:
            pass
    else:
        import signal
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    # Wait for termination
    for _ in range(20):
        if not is_pid_alive(pid):
            break
        time.sleep(0.2)

    # Force kill if still lingering
    if is_pid_alive(pid):
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid), "/T"], check=False, capture_output=True)
        else:
            import signal
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    remove_service_pid(config_dir)
    return True


def restart_service(config_file: Path) -> int:
    """Restart the background service."""
    config_dir = config_file.parent
    stop_service(config_dir)
    time.sleep(0.5)
    return start_service(config_file)


def generate_windows_task_command(config_file: Path) -> str:
    """Generate Windows Task Scheduler command to run watcher on logon."""
    py_exe = sys.executable
    cmd_args = f"-m agent_task_relay.cli --config \\\"{config_file.resolve()}\\\" watch"
    return (
        f'schtasks /Create /SC ONLOGON /TN "AgentTaskRelayWatcher" '
        f'/TR "\\\"{py_exe}\\\" {cmd_args}" /RL HIGHEST /F'
    )


def generate_systemd_unit(config_file: Path) -> str:
    """Generate Linux systemd user service unit definition."""
    py_exe = sys.executable
    cfg_path = config_file.resolve()
    return f"""[Unit]
Description=Agent Task Relay Background Service
After=network.target

[Service]
Type=simple
ExecStart={py_exe} -m agent_task_relay.cli --config {cfg_path} watch
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""


def generate_launchd_plist(config_file: Path) -> str:
    """Generate macOS launchd plist definition."""
    py_exe = sys.executable
    cfg_path = config_file.resolve()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agent-task-relay.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>{py_exe}</string>
        <string>-m</string>
        <string>agent_task_relay.cli</string>
        <string>--config</string>
        <string>{cfg_path}</string>
        <string>watch</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
