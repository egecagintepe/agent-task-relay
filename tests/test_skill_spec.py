"""Tests for Agent Skills specification compliance."""
from pathlib import Path
import unittest


class TestSkillSpecification(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.skill_dir = self.repo_root / "skills" / "agent-task-relay"
        self.skill_file = self.skill_dir / "SKILL.md"

    def test_skill_file_exists(self):
        self.assertTrue(self.skill_file.is_file(), f"SKILL.md missing at {self.skill_file}")

    def test_yaml_frontmatter(self):
        content = self.skill_file.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"), "SKILL.md must start with YAML frontmatter delimiter '---'")

        parts = content.split("---\n", 2)
        self.assertGreaterEqual(len(parts), 3, "SKILL.md must have opening and closing YAML delimiters")

        frontmatter = parts[1]
        self.assertIn("name: agent-task-relay", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("license: PolyForm-Internal-Use-1.0.0", frontmatter)
        self.assertIn("compatibility:", frontmatter)

    def test_referenced_documents_exist(self):
        self.assertTrue((self.skill_dir / "references" / "PROTOCOL.md").is_file())
        self.assertTrue((self.skill_dir / "references" / "SECURITY.md").is_file())
        self.assertTrue((self.skill_dir / "references" / "RUNNERS.md").is_file())
        self.assertTrue((self.skill_dir / "references" / "CHATGPT_SCHEDULING.md").is_file())
        self.assertTrue((self.skill_dir / "assets" / "TASK_TEMPLATE.md").is_file())
        self.assertTrue((self.skill_dir / "assets" / "HELLO_TASK.md").is_file())
        self.assertTrue((self.skill_dir / "scripts" / "relay.py").is_file())


if __name__ == "__main__":
    unittest.main()
