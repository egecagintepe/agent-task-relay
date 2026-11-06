"""Tests for content-bound approvals, rejection, and tamper detection."""
import tempfile
import unittest
from pathlib import Path

from agent_task_relay.config import (
    record_task_approval,
    verify_task_approval,
    load_approved_tasks,
)
from agent_task_relay.protocol.task import parse_task_file


class TestApproval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.tmp.name)

        self.task_file = self.config_dir / "TASK-app-01.md"
        self.task_file.write_text(
            "# TASK-app-01: Original Content\n\n## Objective\nOriginal Objective\n",
            encoding="utf-8",
        )
        self.packet = parse_task_file(self.task_file)

    def tearDown(self):
        self.tmp.cleanup()

    def test_unapproved_task_fails_verification(self):
        approved, reason = verify_task_approval(self.config_dir, self.packet, approval_mode="manual")
        self.assertFalse(approved)
        self.assertIn("has not been approved", reason)

    def test_approved_task_passes_verification(self):
        record_task_approval(self.config_dir, self.packet.task_id, self.packet.sha256)
        approved, reason = verify_task_approval(self.config_dir, self.packet, approval_mode="manual")
        self.assertTrue(approved)
        self.assertIn("matching SHA-256", reason)

    def test_tampered_task_invalidates_approval(self):
        # Step 1: Record approval for original content
        record_task_approval(self.config_dir, self.packet.task_id, self.packet.sha256)

        # Step 2: Tamper with task content
        self.task_file.write_text(
            "# TASK-app-01: Tampered Content\n\n## Objective\nMalicious instruction\n",
            encoding="utf-8",
        )
        tampered_packet = parse_task_file(self.task_file)

        # Step 3: Verification must FAIL and alert about post-approval modification
        approved, reason = verify_task_approval(self.config_dir, tampered_packet, approval_mode="manual")
        self.assertFalse(approved)
        self.assertIn("SECURITY ALERT", reason)
        self.assertIn("modified after approval", reason)

    def test_auto_approval_mode(self):
        approved, reason = verify_task_approval(self.config_dir, self.packet, approval_mode="auto")
        self.assertTrue(approved)


if __name__ == "__main__":
    unittest.main()
