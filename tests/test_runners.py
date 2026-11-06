"""Tests for coding agent runners, registry, sandboxing, and timeouts."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

from agent_task_relay.errors import SecurityError
from agent_task_relay.protocol.models import TaskPacket
from agent_task_relay.runners.base import BaseRunner
from agent_task_relay.runners.custom import CustomCommandRunner
from agent_task_relay.runners.mock import MockRunner
from agent_task_relay.runners.registry import get_runner, list_runners


class TestRunners(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.workspace = self.tmp_path / "workspace"
        self.workspace.mkdir()
        self.log_dir = self.tmp_path / "logs"
        self.log_dir.mkdir()

        self.sample_task = TaskPacket(
            task_id="TASK-test-runner",
            file_path=self.tmp_path / "TASK-test-runner.md",
            raw_content="# Test task",
            sha256="1234567890abcdef",
            byte_size=100,
            title="TASK-test-runner",
            objective="Test runner execution",
        )
        self.sample_task.file_path.write_text("# Test task", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_mock_runner(self):
        runner = MockRunner()
        avail, msg = runner.is_available()
        self.assertTrue(avail)

        result = runner.run(self.sample_task, self.workspace, timeout=10, log_dir=self.log_dir)
        self.assertTrue(result.is_success)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("HELLO received", result.summary)
        self.assertEqual(result.changed_files, [])
        self.assertTrue(Path(result.log_path).is_file())

    def test_custom_runner_disallowed_executable(self):
        runner = CustomCommandRunner(
            command_template=["malicious_binary", "--flag"],
            allowed_executables=["python", "node"],
        )
        avail, msg = runner.is_available()
        self.assertFalse(avail)
        with self.assertRaises(SecurityError):
            runner.run(self.sample_task, self.workspace, timeout=5, log_dir=self.log_dir)

    def test_custom_runner_valid_python_execution(self):
        runner = CustomCommandRunner(
            command_template=[sys.executable, "-c", "print('custom runner ok')"],
            allowed_executables=[Path(sys.executable).name, "python", "python3"],
        )
        avail, _ = runner.is_available()
        self.assertTrue(avail)

        result = runner.run(self.sample_task, self.workspace, timeout=10, log_dir=self.log_dir)
        self.assertTrue(result.is_success)
        self.assertIn("custom runner ok", result.stdout)

    def test_custom_runner_timeout(self):
        # Python command that sleeps longer than timeout
        runner = CustomCommandRunner(
            command_template=[sys.executable, "-c", "import time; time.sleep(3)"],
            allowed_executables=[Path(sys.executable).name, "python", "python3"],
        )
        result = runner.run(self.sample_task, self.workspace, timeout=1, log_dir=self.log_dir)
        self.assertEqual(result.status, "timeout")
        self.assertIn("timed out", result.summary.lower())

    def test_runner_registry_list(self):
        runners = list_runners()
        names = [r["name"] for r in runners]
        self.assertIn("mock", names)
        self.assertIn("agy", names)
        self.assertIn("claude", names)
        self.assertIn("gemini", names)
        self.assertIn("custom", names)

    def test_get_runner(self):
        mock_r = get_runner("mock")
        self.assertIsInstance(mock_r, MockRunner)
        self.assertEqual(mock_r.tier, "verified")

    def test_gemini_runner_availability_and_prompt_construction(self):
        gemini_r = get_runner("gemini")
        self.assertEqual(gemini_r.name, "gemini")
        self.assertEqual(gemini_r.tier, "experimental")

    def test_codex_runner_contract(self):
        codex_r = get_runner("codex")
        self.assertEqual(codex_r.name, "codex")
        self.assertEqual(codex_r.tier, "contract")

    def test_opencode_runner_contract(self):
        opencode_r = get_runner("opencode")
        self.assertEqual(opencode_r.name, "opencode")
        self.assertEqual(opencode_r.tier, "contract")


if __name__ == "__main__":
    unittest.main()
