"""Bridge repository layout, folder validation, and task operations."""
from __future__ import annotations

import json
from pathlib import Path

from agent_task_relay.errors import SecurityError, TransportError
from agent_task_relay.protocol.models import StateRecord, TaskPacket
from agent_task_relay.protocol.task import parse_task_file, validate_task_id, TASK_FILE_PATTERN
from agent_task_relay.transport.git import GitRepo

BRIDGE_FOLDERS = ("inbox", "state", "outbox", "archive")


class Bridge:
    """Manages the private Git bridge repository and its standard folders."""

    def __init__(self, root_path: Path):
        self.root = root_path.expanduser().resolve()
        self.git = GitRepo(self.root)
        self.inbox_dir = self.root / "inbox"
        self.state_dir = self.root / "state"
        self.outbox_dir = self.root / "outbox"
        self.archive_dir = self.root / "archive"

    def validate_integrity(self, check_remote: bool = True) -> None:
        """Validate that the bridge is a safe, root Git repository with real directories."""
        if not self.root.is_dir():
            raise TransportError(f"Bridge directory does not exist: {self.root}")

        if not self.git.is_valid_repo():
            raise TransportError(f"Bridge path is not a valid Git repository: {self.root}")

        real_root = self.git.get_root()
        if real_root != self.root:
            raise SecurityError(
                f"Bridge must be the root of the Git repository, not a subfolder: {self.root} != {real_root}"
            )

        if check_remote and not self.git.has_remote():
            raise TransportError(
                "Bridge checkout has no Git remote configured. Clone a private remote repository first."
            )

        # Check for directory traversal or symlinks in bridge folders
        for folder_name in BRIDGE_FOLDERS:
            folder = self.root / folder_name
            if folder.is_symlink():
                raise SecurityError(f"Unsafe bridge folder (symlink forbidden): {folder}")
            if folder.exists() and not folder.is_dir():
                raise SecurityError(f"Bridge path {folder} must be a directory.")

    def ensure_folders(self) -> list[Path]:
        """Ensure all standard folders exist and have .gitkeep files."""
        keep_files = []
        for folder_name in BRIDGE_FOLDERS:
            folder = self.root / folder_name
            folder.mkdir(parents=True, exist_ok=True)
            keep_file = folder / ".gitkeep"
            if not keep_file.exists():
                keep_file.write_text("", encoding="utf-8")
                keep_files.append(keep_file)
        return keep_files

    def pull(self) -> None:
        """Perform a clean fast-forward pull on the bridge repo."""
        self.validate_integrity(check_remote=False)
        self.git.pull(ff_only=True)

    def list_inbox_tasks(self) -> list[TaskPacket]:
        """Discover and parse valid task packets in the inbox."""
        if not self.inbox_dir.is_dir():
            return []

        packets: list[TaskPacket] = []
        for item in sorted(self.inbox_dir.iterdir()):
            if not item.is_file():
                continue
            if item.is_symlink():
                continue
            if not TASK_FILE_PATTERN.fullmatch(item.name):
                continue

            try:
                packet = parse_task_file(item)
                packets.append(packet)
            except Exception:
                # Malformed or oversized tasks are handled during evaluation
                continue

        return packets

    def get_task_file(self, task_id: str) -> Path | None:
        validate_task_id(task_id)
        path = self.inbox_dir / f"{task_id}.md"
        return path if path.is_file() and not path.is_symlink() else None

    def get_state(self, task_id: str) -> StateRecord | None:
        validate_task_id(task_id)
        state_file = self.state_dir / f"{task_id}.json"
        if not state_file.is_file() or state_file.is_symlink():
            return None
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return StateRecord.from_dict(data)
        except Exception:
            return None

    def write_state(self, record: StateRecord, commit_and_push: bool = True, message: str | None = None) -> Path:
        validate_task_id(record.task_id)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        state_file = self.state_dir / f"{record.task_id}.json"

        # Atomic write
        temp_file = state_file.with_name(f"{state_file.name}.tmp")
        temp_file.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp_file.replace(state_file)

        if commit_and_push:
            rel = str(state_file.relative_to(self.root))
            self.git.add([rel])
            commit_msg = message or f"state: {record.task_id} ({record.status})"
            self.git.commit(commit_msg)
            self.git.push()

        return state_file

    def write_report(
        self,
        task_id: str,
        report_md: str,
        state_record: StateRecord | None = None,
        commit_and_push: bool = True,
        message: str | None = None,
    ) -> Path:
        validate_task_id(task_id)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        report_file = self.outbox_dir / f"{task_id}.result.md"

        # Atomic write
        temp_file = report_file.with_name(f"{report_file.name}.tmp")
        temp_file.write_text(report_md, encoding="utf-8")
        temp_file.replace(report_file)

        to_add = [str(report_file.relative_to(self.root))]

        if state_record is not None:
            state_file = self.state_dir / f"{task_id}.json"
            temp_state = state_file.with_name(f"{state_file.name}.tmp")
            temp_state.write_text(json.dumps(state_record.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            temp_state.replace(state_file)
            to_add.append(str(state_file.relative_to(self.root)))

        if commit_and_push:
            self.git.add(to_add)
            commit_msg = message or f"result: {task_id} ({state_record.status if state_record else 'done'})"
            self.git.commit(commit_msg)
            self.git.push()

        return report_file
