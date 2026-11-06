"""Anthropic Claude Code CLI runner adapter."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import shutil
import subprocess
import time

from agent_task_relay.errors import RunnerError
from agent_task_relay.protocol.models import RunnerResult, TaskPacket
from agent_task_relay.runners.base import BaseRunner
from agent_task_relay.transport.git import GitRepo


class ClaudeCodeRunner(BaseRunner):
    """Runner adapter for Anthropic Claude Code CLI (`claude`)."""

    name = "claude"
    tier = "experimental"
    description = "Anthropic Claude Code CLI non-interactive execution via `claude -p <prompt>`."

    def is_available(self) -> tuple[bool, str]:
        path = shutil.which("claude")
        if not path:
            return False, "Command 'claude' not found in system PATH. Install Claude Code CLI."
        return True, f"Claude Code CLI detected at {path}"

    def run(
        self,
        task: TaskPacket,
        workspace: Path,
        timeout: int,
        log_dir: Path,
        custom_env: dict[str, str] | None = None,
    ) -> RunnerResult:
        if not workspace.is_dir():
            raise RunnerError(f"Workspace directory does not exist: {workspace}")

        prompt = (
            "You are acting as the local coding agent executing an approved task packet. "
            f"Read the task file at {task.file_path.resolve()} and implement its requirements. "
            f"Restrict changes strictly to workspace {workspace.resolve()}. "
            "Run existing tests if safe, and finish with a summary of changed files and test outcomes."
        )

        binary = shutil.which("claude") or "claude"
        command = [binary, "-p", prompt]

        start_dt = dt.datetime.now(dt.timezone.utc)
        start_iso = start_dt.isoformat(timespec="seconds")
        start_mono = time.monotonic()

        stdout = ""
        stderr = ""
        exit_code = 0
        timed_out = False

        try:
            proc = subprocess.run(
                command,
                cwd=str(workspace),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout or ""
            stderr = f"TIMEOUT: Claude Code CLI timed out after {timeout} seconds.\n{exc.stderr or ''}"
            exit_code = -1
        except OSError as exc:
            stderr = f"OS Error starting claude: {exc}"
            exit_code = -2

        duration = round(time.monotonic() - start_mono, 2)
        end_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

        log_path = self.write_log(log_dir, task.task_id, stdout, stderr)

        changed_files: list[str] = []
        repo = GitRepo(workspace)
        if repo.is_valid_repo():
            for line in repo.get_status_porcelain().splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed_files.append(parts[1])

        blockers = self.check_approval_blocks(stdout + "\n" + stderr)

        if timed_out:
            status = "timeout"
            summary = f"Claude Code timed out after {timeout} seconds."
        elif blockers:
            status = "needs-review"
            summary = "Claude Code encountered approval barriers or tool restrictions."
        elif exit_code == 0:
            status = "success"
            summary = stdout.strip()[:2000] if stdout.strip() else "Claude Code completed successfully."
        else:
            status = "failure"
            summary = f"Claude Code failed with code {exit_code}.\n{stderr.strip()[:1000]}"

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
