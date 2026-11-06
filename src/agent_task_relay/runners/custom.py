"""Generic, secure custom command runner."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import shutil
import subprocess
import time

from agent_task_relay.errors import SecurityError, RunnerError
from agent_task_relay.protocol.models import RunnerResult, TaskPacket
from agent_task_relay.runners.base import BaseRunner
from agent_task_relay.transport.git import GitRepo

DEFAULT_ALLOWED_EXECUTABLES = {
    "python", "python3", "node", "npm", "cargo", "go", "ruby", "pytest"
}


class CustomCommandRunner(BaseRunner):
    """Generic custom command runner with strict sandboxing constraints."""

    name = "custom"
    tier = "verified"
    description = "Secure custom command execution using fixed executable allowlists and isolated args."

    def __init__(
        self,
        command_template: list[str] | None = None,
        allowed_executables: list[str] | set[str] | None = None,
    ):
        self.command_template = command_template or []
        self.allowed_executables = set(allowed_executables or DEFAULT_ALLOWED_EXECUTABLES)

    def is_available(self) -> tuple[bool, str]:
        if not self.command_template:
            return False, "Custom runner configured with no command template."
        binary = self.command_template[0]
        binary_base = Path(binary).name.lower()
        if binary_base.endswith(".exe") or binary_base.endswith(".cmd") or binary_base.endswith(".bat"):
            binary_base = binary_base.rsplit(".", 1)[0]

        if binary_base not in self.allowed_executables and binary not in self.allowed_executables:
            return False, f"Executable {binary!r} is not in the allowed list: {sorted(self.allowed_executables)}"

        resolved = shutil.which(binary)
        if not resolved:
            return False, f"Executable {binary!r} not found in system PATH."
        return True, f"Executable found at {resolved}"

    def run(
        self,
        task: TaskPacket,
        workspace: Path,
        timeout: int,
        log_dir: Path,
        custom_env: dict[str, str] | None = None,
    ) -> RunnerResult:
        available, reason = self.is_available()
        if not available:
            raise SecurityError(f"Custom runner cannot execute: {reason}")

        # Build command safely without shell expansion
        cmd: list[str] = []
        for arg in self.command_template:
            replaced = arg.replace("{task_file}", str(task.file_path.resolve()))
            replaced = replaced.replace("{task_id}", task.task_id)
            replaced = replaced.replace("{workspace}", str(workspace.resolve()))
            cmd.append(replaced)

        # Baseline git status in workspace to detect changed files
        repo = GitRepo(workspace)
        initial_clean = False
        initial_status = ""
        if repo.is_valid_repo():
            initial_status = repo.get_status_porcelain()
            initial_clean = repo.is_clean()

        start_dt = dt.datetime.now(dt.timezone.utc)
        start_iso = start_dt.isoformat(timespec="seconds")
        start_mono = time.monotonic()

        env = os.environ.copy()
        if custom_env:
            env.update(custom_env)

        stdout = ""
        stderr = ""
        exit_code = 0
        timed_out = False

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workspace),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                env=env,
                encoding="utf-8",
                errors="replace",
                shell=False,  # strictly non-shell
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout or ""
            stderr = f"TIMEOUT: Custom runner timed out after {timeout} seconds.\n{exc.stderr or ''}"
            exit_code = -1
        except OSError as exc:
            stderr = f"OS Error starting custom command: {exc}"
            exit_code = -2

        duration = round(time.monotonic() - start_mono, 2)
        end_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

        log_path = self.write_log(log_dir, task.task_id, stdout, stderr)

        # Detect changed files if git is available
        changed_files: list[str] = []
        if repo.is_valid_repo():
            final_status = repo.get_status_porcelain()
            for line in final_status.splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed_files.append(parts[1])

        blockers = self.check_approval_blocks(stdout + "\n" + stderr)

        if timed_out:
            status = "timeout"
            summary = f"Custom command timed out after {timeout} seconds."
        elif blockers:
            status = "needs-review"
            summary = "Runner completed with permission blockers or required approvals."
        elif exit_code == 0:
            status = "success"
            summary = stdout.strip()[:2000] if stdout.strip() else "Custom command executed successfully."
        else:
            status = "failure"
            summary = f"Command failed with exit code {exit_code}.\nStderr: {stderr.strip()[:1000]}"

        return RunnerResult(
            runner_name=self.name,
            task_id=task.task_id,
            status=status,
            exit_code=exit_code,
            summary=summary,
            changed_files=changed_files,
            test_results={},
            log_path=str(log_path),
            stdout=stdout,
            stderr=stderr,
            start_time=start_iso,
            end_time=end_iso,
            duration_seconds=duration,
            error_blockers=blockers,
        )
