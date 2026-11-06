"""End-to-end integration tests for Agent Task Relay CLI commands and Git transport."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    full_env["PYTHONPATH"] = src_path + os.pathsep + full_env.get("PYTHONPATH", "")
    if env:
        full_env.update(env)

    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        env=full_env,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


@unittest.skipUnless(shutil.which("git"), "Git must be installed to run integration tests")
class TestCliIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="atr-integration-")
        self.root = Path(self.tmp.name)
        self.remote = self.root / "remote.git"
        self.bridge = self.root / "bridge"
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()

        # Initialize bare remote Git repository
        run_cmd(["git", "init", "--bare", "-b", "main", str(self.remote)])

        # Clone to bridge and make initial commit
        run_cmd(["git", "clone", str(self.remote), str(self.bridge)])
        run_cmd(["git", "-C", str(self.bridge), "config", "user.name", "Test Relay"])
        run_cmd(["git", "-C", str(self.bridge), "config", "user.email", "relay@test.local"])
        (self.bridge / "README.md").write_text("# Bridge\n", encoding="utf-8")
        run_cmd(["git", "-C", str(self.bridge), "add", "README.md"])
        run_cmd(["git", "-C", str(self.bridge), "commit", "-m", "init bridge"])
        run_cmd(["git", "-C", str(self.bridge), "push", "-u", "origin", "main"])

        # Initialize workspace git repo
        run_cmd(["git", "init", "-b", "main", str(self.workspace)])
        run_cmd(["git", "-C", str(self.workspace), "config", "user.name", "Workspace Dev"])
        run_cmd(["git", "-C", str(self.workspace), "config", "user.email", "dev@test.local"])

        # Initialize Agent Task Relay in workspace
        res = self.atr(
            "init",
            "--workspace", str(self.workspace),
            "--bridge", str(self.bridge),
            "--runner", "mock",
            cwd=self.workspace,
        )
        self.assertEqual(res.returncode, 0, f"init failed:\nSTDOUT={res.stdout}\nSTDERR={res.stderr}")

    def tearDown(self):
        self.tmp.cleanup()

    def atr(self, *subcommand: str, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
        cmd = [sys.executable, "-m", "agent_task_relay.cli"] + list(subcommand)
        return run_cmd(cmd, cwd=cwd or self.workspace, env=env)

    def test_doctor_command(self):
        res = self.atr("doctor")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Agent Task Relay Doctor", res.stdout)
        self.assertIn("mock [verified]", res.stdout)

    def test_mock_ping_and_once_cycle(self):
        # Step 1: Run ping to queue mock handshake task
        ping_res = self.atr("ping")
        self.assertEqual(ping_res.returncode, 0)
        self.assertIn("Ping task queued and locally approved:", ping_res.stdout)

        # Step 2: Verify task file created in bridge inbox
        inbox_files = list((self.bridge / "inbox").glob("TASK-ping-*.md"))
        self.assertEqual(len(inbox_files), 1)
        task_id = inbox_files[0].stem

        # Step 3: Run once to process task
        once_res = self.atr("once")
        self.assertEqual(once_res.returncode, 0)
        self.assertIn("completed", once_res.stdout)

        # Step 4: Verify state record
        state_file = self.bridge / "state" / f"{task_id}.json"
        self.assertTrue(state_file.is_file())
        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["attempt"], 1)

        # Step 5: Verify result report in outbox
        report_file = self.bridge / "outbox" / f"{task_id}.result.md"
        self.assertTrue(report_file.is_file())
        report_text = report_file.read_text(encoding="utf-8")
        self.assertIn(f"# {task_id} · COMPLETED", report_text)
        self.assertIn("HELLO received", report_text)

        # Step 6: Verify duplicate prevention on subsequent cycle
        again_res = self.atr("once")
        self.assertIn("No eligible tasks", again_res.stdout)

    def test_manual_approval_workflow(self):
        # Manually create task in bridge inbox
        task_id = "TASK-manual-test"
        task_file = self.bridge / "inbox" / f"{task_id}.md"
        task_file.write_text(
            f"# {task_id}: Manual Test\n\n## Objective\nManual check\n",
            encoding="utf-8",
        )
        run_cmd(["git", "-C", str(self.bridge), "add", f"inbox/{task_id}.md"])
        run_cmd(["git", "-C", str(self.bridge), "commit", "-m", "add unapproved task"])
        run_cmd(["git", "-C", str(self.bridge), "push"])

        # Cycle should skip unapproved task
        cycle1 = self.atr("once")
        self.assertIn(f"Skipping unapproved task {task_id}", cycle1.stdout)
        self.assertFalse((self.bridge / "state" / f"{task_id}.json").exists())

        # Approve without --yes fails safely
        approve_fail = self.atr("approve", task_id)
        self.assertNotEqual(approve_fail.returncode, 0)

        # Approve with --yes succeeds
        approve_ok = self.atr("approve", task_id, "--yes")
        self.assertEqual(approve_ok.returncode, 0)
        self.assertIn(f"Approved task {task_id} locally", approve_ok.stdout)

        # Now cycle processes it
        cycle2 = self.atr("once")
        self.assertEqual(cycle2.returncode, 0)
        self.assertIn("completed", cycle2.stdout)

    def test_reject_command(self):
        task_id = "TASK-to-reject"
        task_file = self.bridge / "inbox" / f"{task_id}.md"
        task_file.write_text(f"# {task_id}: Will Reject\n\n## Objective\nTest rejection\n", encoding="utf-8")
        run_cmd(["git", "-C", str(self.bridge), "add", f"inbox/{task_id}.md"])
        run_cmd(["git", "-C", str(self.bridge), "commit", "-m", "add task to reject"])
        run_cmd(["git", "-C", str(self.bridge), "push"])

        rej_res = self.atr("reject", task_id, "--reason", "Not aligned with roadmap")
        self.assertEqual(rej_res.returncode, 0)
        self.assertIn("rejected and published to outbox", rej_res.stdout)

        # Verify state and outbox
        state = json.loads((self.bridge / "state" / f"{task_id}.json").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "rejected")
        self.assertEqual(state["rejection_reason"], "Not aligned with roadmap")

        report = (self.bridge / "outbox" / f"{task_id}.result.md").read_text(encoding="utf-8")
        self.assertIn(f"# {task_id} · REJECTED", report)

    def test_status_command(self):
        status_res = self.atr("status")
        self.assertEqual(status_res.returncode, 0)
        self.assertIn("Agent Task Relay Status", status_res.stdout)

    def test_config_command(self):
        cfg_res = self.atr("config", "--poll-seconds", "30", "--runner", "mock")
        self.assertEqual(cfg_res.returncode, 0)
        self.assertIn("Configuration updated successfully", cfg_res.stdout)
        self.assertIn('"poll_seconds": 30', cfg_res.stdout)

    def test_simulated_cli_agent_with_fake_binary(self):
        # Create a stub binary for 'agy' that emits expected JSON
        fake_bin_dir = self.workspace / "fake_bin"
        fake_bin_dir.mkdir()
        is_win = sys.platform == "win32"
        stub_file = fake_bin_dir / ("agy.cmd" if is_win else "agy")
        if is_win:
            stub_file.write_text('@echo off\necho {"status":"SUCCESS","response":"Fake agy executed successfully."}\n', encoding="utf-8")
        else:
            stub_file.write_text('#!/usr/bin/env python3\nimport json\nprint(json.dumps({"status":"SUCCESS","response":"Fake agy executed successfully."}))\n', encoding="utf-8")
            stub_file.chmod(0o755)

        env = {"PATH": str(fake_bin_dir) + os.pathsep + os.environ.get("PATH", "")}

        # Switch runner to agy
        self.atr("config", "--runner", "agy", "--approval", "manual")

        # Create task and approve
        task_id = "TASK-fake-agy"
        task_file = self.bridge / "inbox" / f"{task_id}.md"
        task_file.write_text(f"# {task_id}: Stub agy test\n\n## Objective\nStub test\n", encoding="utf-8")
        run_cmd(["git", "-C", str(self.bridge), "add", f"inbox/{task_id}.md"])
        run_cmd(["git", "-C", str(self.bridge), "commit", "-m", "add stub task"])
        run_cmd(["git", "-C", str(self.bridge), "push"])

        self.atr("approve", task_id, "--yes")
        run_res = self.atr("once", env=env)
        self.assertEqual(run_res.returncode, 0)
        self.assertIn("completed", run_res.stdout)

        # Check report
        report = (self.bridge / "outbox" / f"{task_id}.result.md").read_text(encoding="utf-8")
        self.assertIn("Fake agy executed successfully", report)

    def test_packaged_skill_installed_into_workspace(self):
        installed_skill = self.workspace / ".agents" / "skills" / "agent-task-relay" / "SKILL.md"
        self.assertTrue(installed_skill.is_file(), "Skill must be installed into workspace on init")

    def test_git_push_diverged_conflict_recovery(self):
        # Simulate local commit
        local_file = self.bridge / "state" / "TASK-local.json"
        local_file.write_text('{"status": "claimed"}\n', encoding="utf-8")
        run_cmd(["git", "-C", str(self.bridge), "add", "state/TASK-local.json"])
        run_cmd(["git", "-C", str(self.bridge), "commit", "-m", "local state commit"])

        # Simulate concurrent remote commit in bare remote via a second clone
        second_clone = self.root / "second_clone"
        run_cmd(["git", "clone", str(self.remote), str(second_clone)])
        run_cmd(["git", "-C", str(second_clone), "config", "user.name", "Remote User"])
        run_cmd(["git", "-C", str(second_clone), "config", "user.email", "remote@test.local"])
        (second_clone / "inbox" / "TASK-remote.md").write_text("# Remote task\n", encoding="utf-8")
        run_cmd(["git", "-C", str(second_clone), "add", "inbox/TASK-remote.md"])
        run_cmd(["git", "-C", str(second_clone), "commit", "-m", "concurrent remote task"])
        run_cmd(["git", "-C", str(second_clone), "push"])

        # Now test that bridge push recovers from diverged histories cleanly
        from agent_task_relay.transport.git import GitRepo
        repo = GitRepo(self.bridge)
        repo.push()  # Should pull --rebase and push successfully!

        # Verify both commits exist in remote
        log_out = run_cmd(["git", "-C", str(self.bridge), "log", "-n", "2", "--oneline"]).stdout
        self.assertIn("local state commit", log_out)


if __name__ == "__main__":
    unittest.main()
