"""Deterministic mock runner for pipeline validation without LLM tokens."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import time

from agent_task_relay.protocol.models import RunnerResult, TaskPacket
from agent_task_relay.runners.base import BaseRunner


class MockRunner(BaseRunner):
    """Deterministic mock runner that validates end-to-end task transport."""

    name = "mock"
    tier = "verified"
    description = "Deterministic zero-token mock handshake for transport validation."

    def is_available(self) -> tuple[bool, str]:
        return True, "Mock runner is always available (no external dependencies)."

    def run(
        self,
        task: TaskPacket,
        workspace: Path,
        timeout: int,
        log_dir: Path,
        custom_env: dict[str, str] | None = None,
    ) -> RunnerResult:
        start_dt = dt.datetime.now(dt.timezone.utc)
        start_iso = start_dt.isoformat(timespec="seconds")
        start_mono = time.monotonic()

        # Simulate brief internal processing
        time.sleep(0.05)

        duration = round(time.monotonic() - start_mono, 2)
        end_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

        stdout = (
            f"Mock runner processing task: {task.task_id}\n"
            f"Title: {task.title}\n"
            f"Workspace: {workspace}\n"
            f"Objective: {task.objective or 'No explicit objective'}\n"
            f"Status: HELLO received. Transport pipeline verified successfully.\n"
        )
        stderr = ""
        log_path = self.write_log(log_dir, task.task_id, stdout, stderr)

        summary = (
            f"Mock runner: HELLO received for {task.task_id}.\n"
            "Git inbox → watcher → claim → runner → outbox report verified.\n"
            "No AI model invoked. No application code modified."
        )

        return RunnerResult(
            runner_name=self.name,
            task_id=task.task_id,
            status="success",
            exit_code=0,
            summary=summary,
            changed_files=[],
            test_results={"mock_handshake": "PASSED", "verified_transport": True},
            log_path=str(log_path),
            stdout=stdout,
            stderr=stderr,
            start_time=start_iso,
            end_time=end_iso,
            duration_seconds=duration,
            error_blockers=[],
        )
