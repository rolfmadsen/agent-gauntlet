"""Backward-compatibility bridge for EvidenceAuthority (delegating to VerificationReportEngine)."""

from __future__ import annotations

import json

from agent_gauntlet.features.evidence.models import CheckSummary, EvidenceRecord, VerificationReport
from agent_gauntlet.features.evidence.report import VerificationReportEngine


class EvidenceAuthority:
    """Deprecated legacy authority wrapper (all HMAC signing keys removed)."""

    def __init__(self, *args, **kwargs) -> None:
        self._engine = VerificationReportEngine()

    def generate_evidence_json(self, record: EvidenceRecord | VerificationReport) -> str:
        """Serialize record or report to JSON."""
        if isinstance(record, VerificationReport):
            return self._engine.generate_report_json(record)

        data = {
            "task_id": record.task_id,
            "task_title": record.task_title,
            "status": record.status,
            "source_tree_hash": record.source_tree_hash,
            "timestamp": record.timestamp,
            "signature": None,
            "acceptance_criteria": list(record.acceptance_criteria),
            "unresolved_criteria": list(record.unresolved_criteria),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "exit_code": c.exit_code,
                    "duration_seconds": c.duration_seconds,
                }
                for c in record.checks
            ],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def load_evidence_json(cls, json_str: str) -> EvidenceRecord:
        """Deserialize evidence record from JSON."""
        data = json.loads(json_str)
        checks = [
            CheckSummary(
                name=c["name"],
                passed=bool(c.get("passed", c.get("status") == "PASSED")),
                exit_code=int(c.get("exit_code", 0)),
                duration_seconds=float(c.get("duration_seconds", 0.0)),
            )
            for c in data.get("checks", [])
        ]
        return EvidenceRecord(
            task_id=str(data.get("task_id", "")),
            task_title=str(data.get("task_title", "")),
            status=str(data.get("status", data.get("verdict", ""))),
            source_tree_hash=str(
                data.get(
                    "source_tree_hash",
                    data.get("workspace_state", {}).get("source_manifest_digest_post", ""),
                )
            ),
            acceptance_criteria=list(
                data.get(
                    "acceptance_criteria",
                    data.get("task_contract", {}).get("acceptance_criteria", []),
                )
            ),
            unresolved_criteria=list(
                data.get(
                    "unresolved_criteria",
                    data.get("task_contract", {}).get("unresolved_criteria", []),
                )
            ),
            checks=checks,
            timestamp=float(data.get("timestamp", 0.0)),
            signature=data.get("signature"),
        )

    def generate_evidence_markdown(
        self,
        record: EvidenceRecord | VerificationReport,
        head: str = "(no git)",
        source_commit: str = "(no git)",
        title: str = "Evidence Report",
    ) -> str:
        """Render markdown report."""
        if isinstance(record, VerificationReport):
            return self._engine.generate_report_markdown(record, title=title)

        lines = [
            f"# {title}",
            "",
            f"**Task ID**: `{record.task_id}`  ",
        ]
        if record.task_title:
            lines.append(f"**Task Title**: {record.task_title}  ")
        lines.extend(
            [
                f"**Status**: `{record.status}`  ",
                f"**Source Tree Hash**: `{record.source_tree_hash}`  ",
                f"**Head**: `{head}`  ",
                f"**Source Commit**: `{source_commit}`  ",
            ]
        )
        if record.acceptance_criteria:
            lines.extend(["", "## Acceptance Criteria", ""])
            for crit in record.acceptance_criteria:
                status_icon = "[x]" if crit not in record.unresolved_criteria else "[ ]"
                lines.append(f"- {status_icon} {crit}")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Verification Checks",
                "",
                "| Check Name | Status | Exit Code | Duration (s) |",
                "|---|---|---|---|",
            ]
        )
        for c in record.checks:
            lines.append(
                f"| `{c.name}` | `{c.status}` | `{c.exit_code}` | `{c.duration_seconds:.3f}s` |"
            )

        lines.extend(["", "---", ""])
        return "\n".join(lines)
