"""Tests for OKF (Open Knowledge Format v0.2) parsing, validation, and stamping."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_gauntlet.features.okf.models import Actor
from agent_gauntlet.features.okf.stamper import stamp_okf_content
from agent_gauntlet.features.okf.validator import (
    parse_frontmatter,
    validate_okf_metadata,
    validate_okf_workspace,
)


class TestOkfModels(unittest.TestCase):
    """Test OKF domain models."""

    def test_actor_parsing(self):
        human = Actor.parse("human:alice")
        self.assertEqual(human.kind, "human")
        self.assertEqual(human.identifier, "alice")
        self.assertEqual(human.raw, "human:alice")

        agent = Actor.parse("antigravity/gemini-3.7-flash")
        self.assertEqual(agent.kind, "agent")
        self.assertEqual(agent.identifier, "gemini-3.7-flash")
        self.assertEqual(agent.namespace, "antigravity")

        process = Actor.parse("process:agent-gauntlet-verify")
        self.assertEqual(process.kind, "process")
        self.assertEqual(process.identifier, "agent-gauntlet-verify")

    def test_invalid_actor_parsing(self):
        with self.assertRaises(ValueError):
            Actor.parse("invalid_no_prefix_or_slash")
        with self.assertRaises(ValueError):
            Actor.parse("human:")
        with self.assertRaises(ValueError):
            Actor.parse("/gemini")


class TestOkfFrontmatterParsing(unittest.TestCase):
    """Test extracting and parsing frontmatter."""

    def test_parse_valid_frontmatter(self):
        content = """---
type: Task Package
title: My Task
status: draft
---
# Body content
Some text here.
"""
        meta, body, error = parse_frontmatter(content)
        self.assertIsNone(error)
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta["type"], "Task Package")
        self.assertEqual(meta["title"], "My Task")
        self.assertEqual(meta["status"], "draft")
        self.assertEqual(body.strip(), "# Body content\nSome text here.")

    def test_parse_no_frontmatter(self):
        content = "# Just a markdown file\nNo frontmatter."
        meta, body, error = parse_frontmatter(content)
        self.assertIsNone(error)
        self.assertIsNone(meta)
        self.assertEqual(body, content)

    def test_parse_unclosed_frontmatter(self):
        content = "---\ntype: Task\ntitle: Broken"
        meta, _body, error = parse_frontmatter(content)
        self.assertIsNone(meta)
        self.assertIn("Unclosed", str(error))

    def test_parse_invalid_yaml(self):
        content = "---\ntype: [invalid: yaml: : : : \n---\nBody"
        meta, _body, error = parse_frontmatter(content)
        self.assertIsNone(meta)
        self.assertIsNotNone(error)


class TestOkfValidationRules(unittest.TestCase):
    """Test strict OKF v0.2 validation rules."""

    def setUp(self):
        self.now = datetime(2026, 8, 23, 15, 30, 0, tzinfo=timezone.utc)

    def test_validate_valid_minimal_document(self):
        meta = {"type": "Task Package"}
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertEqual(len(findings), 0)

    def test_validate_missing_type_fails(self):
        meta = {"title": "Missing Type"}
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertTrue(any(f.rule == "REQUIRED_TYPE" for f in findings))

    def test_validate_empty_type_fails(self):
        meta = {"type": "   "}
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertTrue(any(f.rule == "REQUIRED_TYPE" for f in findings))

    def test_validate_status_enum(self):
        for valid_status in ["draft", "stable", "deprecated"]:
            findings = validate_okf_metadata(
                {"type": "Task", "status": valid_status},
                file_path="task.md",
                now=self.now,
            )
            self.assertEqual(len(findings), 0)

        findings = validate_okf_metadata(
            {"type": "Task", "status": "in_progress"},
            file_path="task.md",
            now=self.now,
        )
        self.assertTrue(any(f.rule == "INVALID_STATUS" for f in findings))

    def test_validate_generated_block(self):
        meta = {
            "type": "Task Package",
            "generated": {
                "by": "antigravity/gemini-3.7-flash",
                "at": "2026-08-23T15:00:00Z",
            },
        }
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertEqual(len(findings), 0)

    def test_validate_generated_invalid_actor(self):
        meta = {
            "type": "Task Package",
            "generated": {
                "by": "just-a-name",
                "at": "2026-08-23T15:00:00Z",
            },
        }
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertTrue(any(f.rule == "INVALID_ACTOR" for f in findings))

    def test_validate_generated_future_timestamp(self):
        future_time = (self.now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        meta = {
            "type": "Task Package",
            "generated": {
                "by": "human:alice",
                "at": future_time,
            },
        }
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertTrue(any(f.rule == "FUTURE_TIMESTAMP" for f in findings))

    def test_validate_temporal_sequence_verified_before_generated(self):
        meta = {
            "type": "Task Package",
            "generated": {
                "by": "antigravity/gemini-3.7-flash",
                "at": "2026-08-23T15:00:00Z",
            },
            "verified": [
                {
                    "by": "human:alice",
                    "at": "2026-08-23T14:00:00Z",  # 1 hour before generation!
                }
            ],
        }
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertTrue(any(f.rule == "CHRONOLOGICAL_INVERSION" for f in findings))

    def test_validate_verified_bare_mapping(self):
        meta = {
            "type": "Task Package",
            "generated": {
                "by": "antigravity/gemini-3.7-flash",
                "at": "2026-08-23T15:00:00Z",
            },
            "verified": {
                "by": "human:alice",
                "at": "2026-08-23T15:10:00Z",
            },
        }
        findings = validate_okf_metadata(meta, file_path="tasks/001.md", now=self.now)
        self.assertEqual(len(findings), 0)

    def test_validate_stale_after(self):
        meta = {
            "type": "Spec",
            "stale_after": "2026-12-31T23:59:59Z",
        }
        findings = validate_okf_metadata(meta, file_path="spec.md", now=self.now)
        self.assertEqual(len(findings), 0)

        meta_bad = {
            "type": "Spec",
            "stale_after": "invalid-date",
        }
        findings_bad = validate_okf_metadata(meta_bad, file_path="spec.md", now=self.now)
        self.assertTrue(any(f.rule == "INVALID_TIMESTAMP" for f in findings_bad))

    def test_validate_sources_list(self):
        meta = {
            "type": "Task",
            "sources": [
                {
                    "id": "adr-0001",
                    "resource": "/docs/adr/0001-test.md",
                    "title": "ADR 1",
                }
            ],
        }
        findings = validate_okf_metadata(meta, file_path="task.md", now=self.now)
        self.assertEqual(len(findings), 0)

        meta_invalid = {
            "type": "Task",
            "sources": [
                {
                    "id": "adr-0001",
                    # missing required resource!
                    "title": "ADR 1",
                }
            ],
        }
        findings_invalid = validate_okf_metadata(
            meta_invalid, file_path="task.md", now=self.now
        )
        self.assertTrue(any(f.rule == "SOURCE_MISSING_RESOURCE" for f in findings_invalid))


class TestOkfStamper(unittest.TestCase):
    """Test stamping and updating OKF frontmatter."""

    def test_stamp_new_frontmatter_on_bare_markdown(self):
        original = "# Bare Markdown\nHello world"
        stamped = stamp_okf_content(
            original,
            doc_type="Task Package",
            status="draft",
            generated_by="antigravity/gemini-3.7-flash",
            generated_at="2026-08-23T15:00:00Z",
        )
        meta, body, err = parse_frontmatter(stamped)
        self.assertIsNone(err)
        assert meta is not None
        self.assertEqual(meta["type"], "Task Package")
        self.assertEqual(meta["status"], "draft")
        self.assertEqual(meta["generated"]["by"], "antigravity/gemini-3.7-flash")
        self.assertEqual(body.strip(), original.strip())

    def test_stamp_add_verification_and_update_status(self):
        original = """---
type: Task Package
title: Existing Task
status: draft
generated: { by: antigravity/gemini-3.7-flash, at: "2026-08-23T15:00:00Z" }
tags: [core, cli]
---
# Original Body
Preserved exactly.
"""
        stamped = stamp_okf_content(
            original,
            status="stable",
            verified_by="human:alice",
            verified_at="2026-08-23T15:15:00Z",
        )
        meta, body, err = parse_frontmatter(stamped)
        self.assertIsNone(err)
        assert meta is not None
        self.assertEqual(meta["status"], "stable")
        self.assertEqual(meta["title"], "Existing Task")
        self.assertEqual(meta["tags"], ["core", "cli"])
        self.assertEqual(len(meta["verified"]), 1)
        self.assertEqual(meta["verified"][0]["by"], "human:alice")
        self.assertEqual(meta["verified"][0]["at"], "2026-08-23T15:15:00Z")
        self.assertIn("# Original Body\nPreserved exactly.", body)


class TestOkfWorkspaceValidator(unittest.TestCase):
    """Test validating workspace files."""

    def test_workspace_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "tasks").mkdir()
            (tmppath / "docs/adr").mkdir(parents=True)

            valid_task = """---
type: Task Package
title: Valid Task
status: draft
generated: { by: antigravity/gemini-3.7-flash, at: "2026-08-23T15:00:00Z" }
---
# Valid Task
"""
            (tmppath / "tasks/001-task.md").write_text(valid_task)

            invalid_adr = """---
title: Missing Type
---
# Broken ADR
"""
            (tmppath / "docs/adr/0001-test.md").write_text(invalid_adr)

            now = datetime(2026, 8, 23, 15, 30, 0, tzinfo=timezone.utc)
            report = validate_okf_workspace(tmppath, ["tasks", "docs/adr"], now=now)
            self.assertFalse(report.valid)
            self.assertEqual(report.total_files, 2)
            self.assertEqual(report.valid_files, 1)
            self.assertEqual(len(report.findings), 1)
            self.assertEqual(report.findings[0].rule, "REQUIRED_TYPE")


if __name__ == "__main__":
    unittest.main()
