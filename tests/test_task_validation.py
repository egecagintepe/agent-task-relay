"""Tests for Task ID validation, schema parsing, and boundary checks."""
import tempfile
import unittest
from pathlib import Path

from agent_task_relay.errors import TaskValidationError, SecurityError
from agent_task_relay.protocol.task import (
    validate_task_id,
    validate_task_file_name,
    parse_task_file,
    MAX_TASK_BYTES,
)


class TestTaskValidation(unittest.TestCase):
    def test_valid_task_ids(self):
        valid_ids = [
            "TASK-001",
            "TASK-auth-v2",
            "TASK-bug.fix_123",
            "TASK-feature-alpha-beta-gamma",
            "TASK-1",
        ]
        for tid in valid_ids:
            self.assertEqual(validate_task_id(tid), tid)

    def test_invalid_task_ids(self):
        invalid_ids = [
            "",
            "task-001",  # lowercase prefix
            "TASK",      # no hyphen/id
            "TASK-",     # empty suffix
            "TASK-001/escape",  # slash
            "TASK-001\\escape", # backslash
            "TASK-..",          # traversal
            "TASK-" + ("a" * 81), # exceeds max 85 chars total
        ]
        for tid in invalid_ids:
            with self.assertRaises((TaskValidationError, SecurityError)):
                validate_task_id(tid)

    def test_validate_task_file_name(self):
        self.assertEqual(validate_task_file_name("TASK-001.md"), "TASK-001")
        with self.assertRaises(TaskValidationError):
            validate_task_file_name("TASK-001.txt")
        with self.assertRaises(TaskValidationError):
            validate_task_file_name("README.md")

    def test_parse_valid_task_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f_path = Path(tmp_dir) / "TASK-001.md"
            f_path.write_text(
                "# TASK-001: Sample Title\n\n"
                "## Objective\nDo something useful\n\n"
                "## Context\nSome context\n\n"
                "## Scope\nAllowed scope\n\n"
                "## Acceptance criteria\n- [ ] Requirement 1\n- [x] Requirement 2\n",
                encoding="utf-8",
            )
            packet = parse_task_file(f_path)
            self.assertEqual(packet.task_id, "TASK-001")
            self.assertEqual(packet.title, "TASK-001: Sample Title")
            self.assertEqual(packet.objective, "Do something useful")
            self.assertEqual(packet.context, "Some context")
            self.assertEqual(packet.scope, "Allowed scope")
            self.assertEqual(len(packet.acceptance_criteria), 2)
            self.assertTrue(len(packet.sha256) == 64)

    def test_parse_empty_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f_path = Path(tmp_dir) / "TASK-empty.md"
            f_path.write_text("", encoding="utf-8")
            with self.assertRaises(TaskValidationError):
                parse_task_file(f_path)

    def test_parse_oversized_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f_path = Path(tmp_dir) / "TASK-big.md"
            f_path.write_text("a" * (MAX_TASK_BYTES + 10), encoding="utf-8")
            with self.assertRaises(TaskValidationError):
                parse_task_file(f_path)


if __name__ == "__main__":
    unittest.main()
