"""Tests for security boundaries, path traversal prevention, and secret redaction."""
import tempfile
import unittest
from pathlib import Path

from agent_task_relay.errors import SecurityError, TaskValidationError
from agent_task_relay.protocol.task import validate_task_id, parse_task_file
from agent_task_relay.transport.redactor import redact_secrets, sanitize_markdown_fences


class TestSecurity(unittest.TestCase):
    def test_path_traversal_in_task_id_rejected(self):
        with self.assertRaises(SecurityError):
            validate_task_id("TASK-../../etc/passwd")
        with self.assertRaises(SecurityError):
            validate_task_id("TASK-..\\windows\\system32")
        with self.assertRaises(SecurityError):
            validate_task_id("TASK-\0nullbyte")

    def test_symlinks_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            real_file = tmp / "real.txt"
            real_file.write_text("# TASK-sym: Title\n\n## Objective\nTest", encoding="utf-8")
            symlink = tmp / "TASK-sym.md"
            try:
                symlink.symlink_to(real_file)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks not supported on this host/privilege")

            with self.assertRaises(SecurityError):
                parse_task_file(symlink)

    def test_secret_redaction_github_token(self):
        raw = "User token is ghp_1234567890abcdef1234567890 for repo"
        redacted = redact_secrets(raw)
        self.assertNotIn("ghp_1234567890abcdef1234567890", redacted)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", redacted)

    def test_secret_redaction_openai_key(self):
        raw = "OpenAI key: sk-abcdefghijklmnopqrstuvwxyz123456"
        redacted = redact_secrets(raw)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", redacted)
        self.assertIn("[REDACTED_API_KEY]", redacted)

    def test_secret_redaction_anthropic_key(self):
        raw = "Using key sk-ant-api03-abcdefghijklmnopqrstuvwxyz"
        redacted = redact_secrets(raw)
        self.assertNotIn("sk-ant-api03-abcdefghijklmnopqrstuvwxyz", redacted)
        self.assertIn("[REDACTED_ANTHROPIC_KEY]", redacted)

    def test_secret_redaction_aws_key(self):
        raw = "AWS credentials: AKIAIOSFODNN7EXAMPLE"
        redacted = redact_secrets(raw)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", redacted)
        self.assertIn("[REDACTED_AWS_KEY]", redacted)

    def test_secret_redaction_private_key(self):
        raw = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA0Y1m23...\n"
            "-----END RSA PRIVATE KEY-----"
        )
        redacted = redact_secrets(raw)
        self.assertNotIn("MIIEowIBAAKCAQEA0Y1m23...", redacted)
        self.assertIn("[REDACTED_PRIVATE_KEY]", redacted)

    def test_secret_redaction_generic_key_value(self):
        raw = "config: api_key='supersecretpassword123', password: 'mysecretpassword'"
        redacted = redact_secrets(raw)
        self.assertNotIn("supersecretpassword123", redacted)
        self.assertNotIn("mysecretpassword", redacted)
        self.assertIn("api_key=[REDACTED]", redacted)

    def test_markdown_fence_sanitization(self):
        raw = "Here is some code ```python print('hi') ``` inside agent text"
        sanitized = sanitize_markdown_fences(raw)
        self.assertNotIn("```", sanitized)
        self.assertIn("'''", sanitized)


if __name__ == "__main__":
    unittest.main()
