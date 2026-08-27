"""Unit and invariant tests for task parsing and domain contracts."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.tasks.models import TaskStatus
from agent_gauntlet.features.tasks.parser import (
    is_task_active,
    parse_task_status,
    resolve_task_contract,
)


class TestTaskDomain(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir)
        self.tasks_dir = self.workspace / "tasks"
        self.tasks_dir.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_task_status_explicit_formats(self) -> None:
        self.assertEqual(parse_task_status("**Status**: `ACTIVE`"), TaskStatus.ACTIVE)
        self.assertEqual(parse_task_status("Status: ACTIVE"), TaskStatus.ACTIVE)
        self.assertEqual(parse_task_status("**Status**: `DONE`"), TaskStatus.DONE)
        self.assertEqual(parse_task_status("**Status**: `DRAFT`"), TaskStatus.DRAFT)
        self.assertEqual(parse_task_status("**Status**: `REJECTED`"), TaskStatus.REJECTED)
        self.assertEqual(parse_task_status("**Status**: `REOPENED`"), TaskStatus.REOPENED)
        self.assertEqual(parse_task_status("**Status**: `IN_PROGRESS`"), TaskStatus.IN_PROGRESS)
        self.assertEqual(parse_task_status("No status here"), TaskStatus.UNKNOWN)

    def test_is_task_active_only_allowed_statuses(self) -> None:
        # Allowed active statuses: ACTIVE, IN_PROGRESS, IN-PROGRESS, WIP, TODO, REOPENED
        active_doc = "# Task 001\n**Status**: `ACTIVE`\n\n- [ ] criterion 1"
        self.assertTrue(is_task_active(active_doc))

        reopened_doc = "# Task 001\n**Status**: `REOPENED`\n\n- [ ] criterion 1"
        self.assertTrue(is_task_active(reopened_doc))

        # Disallowed/inactive statuses must NOT be active even if they contain checkboxes
        draft_doc = "# Task 001\n**Status**: `DRAFT`\n\n- [ ] criterion 1"
        self.assertFalse(is_task_active(draft_doc))

        rejected_doc = "# Task 001\n**Status**: `REJECTED`\n\n- [ ] criterion 1"
        self.assertFalse(is_task_active(rejected_doc))

        done_doc = "# Task 001\n**Status**: `DONE`\n\n- [x] criterion 1"
        self.assertFalse(is_task_active(done_doc))

        no_status_doc = "# Task 001\n\n- [ ] criterion 1"
        self.assertFalse(is_task_active(no_status_doc))

        no_criteria_active = "# Task 001\n**Status**: `ACTIVE`\n\nNo criteria section"
        self.assertFalse(is_task_active(no_criteria_active))

    def test_resolve_task_contract_finds_active_task(self) -> None:
        task_file = self.tasks_dir / "001-test.md"
        task_file.write_text(
            "# Task 1: My Title\n**Status**: `ACTIVE`\n\n- [x] done crit\n- [ ] open crit\n",
            encoding="utf-8",
        )

        task_id, title, criteria, unresolved = resolve_task_contract(self.workspace)
        self.assertEqual(task_id, "001-test")
        self.assertEqual(title, "Task 1: My Title")
        self.assertEqual(criteria, ["done crit", "open crit"])
        self.assertEqual(unresolved, ["open crit"])


if __name__ == "__main__":
    unittest.main()
