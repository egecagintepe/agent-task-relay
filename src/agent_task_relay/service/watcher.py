"""Task watcher and polling loop engine."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import signal
import socket
import sys
import time
from typing import Callable

from agent_task_relay.config import RelayConfig, verify_task_approval
from agent_task_relay.errors import (
    RelayError,
    SecurityError,
    StateTransitionError,
    TransportError,
    TaskValidationError,
)
from agent_task_relay.protocol.models import StateRecord, TaskState
from agent_task_relay.protocol.report import generate_result_report
from agent_task_relay.protocol.state_machine import TaskStateMachine
from agent_task_relay.runners.registry import get_runner
from agent_task_relay.service.lock import acquire_process_lock
from agent_task_relay.transport.bridge import Bridge


class TaskWatcher:
    """Core watcher engine for the Agent Task Relay."""

    def __init__(self, config_path: Path, config: RelayConfig):
        self.config_path = config_path.resolve()
        self.config_dir = self.config_path.parent
        self.config = config
        self.bridge = Bridge(Path(config.bridge))
        self.workspace = Path(config.workspace).resolve()
        self.stop_requested = False

    def now_iso(self) -> str:
        return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    def run_single_cycle(self) -> bool:
        """Execute one polling and execution cycle. Returns True if a task was processed."""
        self.bridge.validate_integrity(check_remote=False)

        try:
            self.bridge.pull()
        except TransportError as exc:
            print(f"[WARN] Failed to pull bridge: {exc}", file=sys.stderr)
            return False

        inbox_tasks = self.bridge.list_inbox_tasks()
        if not inbox_tasks:
            return False

        for task in inbox_tasks:
            task_id = task.task_id
            state = self.bridge.get_state(task_id)

            # Check if task is already in terminal state
            if state is not None:
                if state.status in [s.value for s in TaskState.terminal_states()]:
                    continue

                if state.status == TaskState.CLAIMED.value or state.status == TaskState.RUNNING.value:
                    # An interrupted task from a previous crash: do not silently re-run!
                    print(
                        f"[WARN] Task {task_id} was already claimed at {state.claimed_at} by host {state.host}. "
                        "Silently re-running claimed tasks is disabled to prevent duplicate side-effects. "
                        "Review workspace changes and create a new task ID if retry is needed.",
                        file=sys.stderr,
                    )
                    continue

            # Verify human / policy approval
            approved, reason = verify_task_approval(self.config_dir, task, self.config.approval_mode)
            if not approved:
                print(f"[INFO] Skipping unapproved task {task_id}: {reason}")
                continue

            # Validate state transition from PENDING -> CLAIMED
            TaskStateMachine.validate_transition(task_id, TaskState.PENDING, TaskState.CLAIMED)

            # Step 1: Claim task and persist to remote bridge BEFORE running the agent
            hostname = socket.gethostname()
            claim_record = StateRecord(
                task_id=task_id,
                status=TaskState.CLAIMED.value,
                sha256=task.sha256,
                claimed_at=self.now_iso(),
                host=hostname,
                attempt=1,
                runner=self.config.runner,
            )

            try:
                self.bridge.write_state(
                    claim_record,
                    commit_and_push=True,
                    message=f"claim: {task_id} ({self.config.runner})",
                )
            except TransportError as exc:
                print(
                    f"[ERROR] Failed to push claim for {task_id} to remote bridge: {exc}. "
                    "Task will NOT be executed.",
                    file=sys.stderr,
                )
                return False

            print(f"[INFO] Claimed {task_id}. Dispatching to runner: {self.config.runner} ...", flush=True)

            # Step 2: Dispatch task to runner
            runner = get_runner(self.config.runner, self.config)
            log_dir = self.config_dir / "logs"

            start_mono = time.monotonic()
            runner_result = runner.run(
                task=task,
                workspace=self.workspace,
                timeout=self.config.timeout_seconds,
                log_dir=log_dir,
            )
            duration = round(time.monotonic() - start_mono, 2)

            # Map runner outcome to valid TaskState
            if runner_result.status == "success":
                target_state = TaskState.COMPLETED
            elif runner_result.status == "needs-review":
                target_state = TaskState.NEEDS_REVIEW
            else:
                target_state = TaskState.FAILED

            TaskStateMachine.validate_transition(task_id, TaskState.CLAIMED, target_state)

            # Step 3: Check for remote state changes while agent ran
            try:
                self.bridge.pull()
            except TransportError:
                pass

            refreshed_state = self.bridge.get_state(task_id)
            if refreshed_state and (refreshed_state.status != TaskState.CLAIMED.value or refreshed_state.sha256 != task.sha256):
                raise RelayError(
                    f"State for {task_id} unexpectedly modified during execution. Manual inspection required."
                )

            # Step 4: Publish result report and final state
            final_record = StateRecord(
                task_id=task_id,
                status=target_state.value,
                sha256=task.sha256,
                claimed_at=claim_record.claimed_at,
                host=hostname,
                attempt=1,
                runner=self.config.runner,
                started_at=runner_result.start_time,
                finished_at=runner_result.end_time or self.now_iso(),
                duration_seconds=duration,
                changed_files=runner_result.changed_files,
                error=runner_result.summary if not runner_result.is_success else None,
            )

            report_content = generate_result_report(task_id, final_record, runner_result)
            self.bridge.write_report(
                task_id=task_id,
                report_md=report_content,
                state_record=final_record,
                commit_and_push=True,
                message=f"result: {task_id} ({target_state.value})",
            )

            print(f"[INFO] Published result for {task_id}: {target_state.value} ({duration}s)", flush=True)
            return True

        return False

    def watch(self, on_cycle: Callable[[], None] | None = None) -> None:
        """Run foreground polling loop."""
        interval = max(5, int(self.config.poll_seconds))
        print(
            f"Agent Task Relay active.\n"
            f"Bridge: {self.config.bridge}\n"
            f"Workspace: {self.config.workspace}\n"
            f"Runner: {self.config.runner}\n"
            f"Approval mode: {self.config.approval_mode}\n"
            f"Polling interval: {interval}s\n"
            "Press Ctrl+C to stop.\n"
        )

        def sig_handler(sig, frame):
            print("\nGracefully shutting down watcher...", flush=True)
            self.stop_requested = True

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        with acquire_process_lock(self.config_dir):
            while not self.stop_requested:
                try:
                    self.run_single_cycle()
                except Exception as exc:
                    print(f"[WARN] Error during poll cycle: {exc}", file=sys.stderr, flush=True)

                if on_cycle:
                    on_cycle()

                # Sleep in short increments for responsive interrupt handling
                for _ in range(interval * 2):
                    if self.stop_requested:
                        break
                    time.sleep(0.5)

        print("Watcher stopped cleanly.")
