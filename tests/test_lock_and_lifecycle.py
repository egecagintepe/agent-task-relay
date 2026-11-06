"""Tests for process locking, stale lock recovery, and service lifecycle."""
import os
from pathlib import Path
import tempfile
import unittest

from agent_task_relay.config import RelayConfig, save_config
from agent_task_relay.errors import LockError
from agent_task_relay.service.lifecycle import (
    start_service,
    stop_service,
    get_service_status,
    generate_windows_task_command,
    generate_systemd_unit,
    generate_launchd_plist,
)
from agent_task_relay.service.lock import acquire_process_lock, is_pid_alive


class TestLockAndLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.tmp.name) / ".agent-task-relay"
        self.config_dir.mkdir()
        self.cfg_file = self.config_dir / "config.json"

        bridge_dir = Path(self.tmp.name) / "bridge"
        workspace_dir = Path(self.tmp.name) / "workspace"
        bridge_dir.mkdir()
        workspace_dir.mkdir()

        self.cfg = RelayConfig(
            bridge=str(bridge_dir),
            workspace=str(workspace_dir),
            runner="mock",
        )
        save_config(self.cfg_file, self.cfg)

    def tearDown(self):
        self.tmp.cleanup()

    def test_acquire_and_release_lock(self):
        lock_path = self.config_dir / "run.lock"
        self.assertFalse(lock_path.exists())

        with acquire_process_lock(self.config_dir):
            self.assertTrue(lock_path.exists())
            self.assertTrue((lock_path / "owner.txt").is_file())

        self.assertFalse(lock_path.exists())

    def test_stale_lock_recovery(self):
        lock_path = self.config_dir / "run.lock"
        lock_path.mkdir()
        # Non-existent dead PID
        (lock_path / "owner.txt").write_text("99999999 dummy 2026-01-01T00:00:00\n", encoding="utf-8")

        # Must automatically reclaim stale lock
        with acquire_process_lock(self.config_dir):
            self.assertTrue(lock_path.exists())

        self.assertFalse(lock_path.exists())

    def test_service_status_when_stopped(self):
        status = get_service_status(self.config_dir)
        self.assertFalse(status["running"])
        self.assertIsNone(status["pid"])

    def test_service_templates_generation(self):
        win_cmd = generate_windows_task_command(self.cfg_file)
        self.assertIn("schtasks /Create", win_cmd)
        self.assertIn("AgentTaskRelayWatcher", win_cmd)

        sysd = generate_systemd_unit(self.cfg_file)
        self.assertIn("[Unit]", sysd)
        self.assertIn("ExecStart=", sysd)

        plist = generate_launchd_plist(self.cfg_file)
        self.assertIn("<plist version=\"1.0\">", plist)
        self.assertIn("com.agent-task-relay.watcher", plist)


if __name__ == "__main__":
    unittest.main()
