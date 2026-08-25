"""Unsigned verification report engine and markdown generator for agent-gauntlet (Schema v2)."""

from __future__ import annotations

import hmac
import json

from agent_gauntlet.features.evidence.models import (
    CheckSummary,
    ExecutionMetadata,
    TaskContract,
    VcsMetadata,
    VerificationReport,
    WorkspaceState,
)


class VerificationReportEngine:
    """Engine for generating, serializing, and inspecting unsigned verification reports."""

    def generate_report_json(self, report: VerificationReport) -> str:
        """Serialize verification report to canonical Schema v2 JSON."""
        vcs_dict = None
        if report.workspace_state.vcs:
            vcs_dict = {
                "type": report.workspace_state.vcs.type,
                "head": report.workspace_state.vcs.head,
                "commit": report.workspace_state.vcs.commit,
                "is_dirty": report.workspace_state.vcs.is_dirty,
            }

        data = {
            "$schema": "https://agent-gauntlet.dev/schemas/v2/verification-report.json",
            "schema_version": report.schema_version,
            "execution_origin": report.execution_origin,
            "verdict": report.verdict,
            "task_contract": {
                "task_id": report.task_contract.task_id,
                "task_title": report.task_contract.task_title,
                "task_digest": report.task_contract.task_digest,
                "acceptance_criteria": list(report.task_contract.acceptance_criteria),
                "unresolved_criteria": list(report.task_contract.unresolved_criteria),
            },
            "workspace_state": {
                "manifest_version": report.workspace_state.manifest_version,
                "source_content_digest": report.workspace_state.source_content_digest,
                "source_manifest_digest_pre": report.workspace_state.source_manifest_digest_pre,
                "source_manifest_digest_post": report.workspace_state.source_manifest_digest_post,
                "config_digest": report.workspace_state.config_digest,
                "policy_digest": report.workspace_state.policy_digest,
                "check_definitions_digest": report.workspace_state.check_definitions_digest,
                "included_files_count": report.workspace_state.included_files_count,
                "vcs": vcs_dict,
            },
            "execution_metadata": {
                "started_at": report.execution_metadata.started_at,
                "finished_at": report.execution_metadata.finished_at,
                "total_duration_seconds": round(report.execution_metadata.total_duration_seconds, 3),
                "environment": report.execution_metadata.environment,
            },
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "exit_code": c.exit_code,
                    "duration_seconds": round(c.duration_seconds, 3),
                    "optional": c.optional,
                    "log_digest": c.log_digest,
                }
                for c in report.checks
            ],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def load_report_json(cls, json_str: str) -> VerificationReport:
        """Deserialize verification report from JSON (Schema v2 or legacy format)."""
        data = json.loads(json_str)

        # Handle Schema v2
        if "schema_version" in data or "workspace_state" in data:
            task_dict = data.get("task_contract", {})
            task_contract = TaskContract(
                task_id=str(task_dict.get("task_id", "")),
                task_title=str(task_dict.get("task_title", "")),
                task_digest=str(task_dict.get("task_digest", "")),
                acceptance_criteria=list(task_dict.get("acceptance_criteria", [])),
                unresolved_criteria=list(task_dict.get("unresolved_criteria", [])),
            )

            ws_dict = data.get("workspace_state", {})
            vcs_dict = ws_dict.get("vcs")
            vcs_obj = None
            if isinstance(vcs_dict, dict):
                vcs_obj = VcsMetadata(
                    type=str(vcs_dict.get("type", "git")),
                    head=str(vcs_dict.get("head", "")),
                    commit=str(vcs_dict.get("commit", "")),
                    is_dirty=bool(vcs_dict.get("is_dirty", False)),
                )

            workspace_state = WorkspaceState(
                manifest_version=str(ws_dict.get("manifest_version", "1.0")),
                source_content_digest=str(ws_dict.get("source_content_digest", "")),
                source_manifest_digest_pre=str(ws_dict.get("source_manifest_digest_pre", "")),
                source_manifest_digest_post=str(ws_dict.get("source_manifest_digest_post", "")),
                config_digest=str(ws_dict.get("config_digest", "")),
                policy_digest=str(ws_dict.get("policy_digest", "")),
                check_definitions_digest=str(ws_dict.get("check_definitions_digest", "")),
                included_files_count=int(ws_dict.get("included_files_count", 0)),
                vcs=vcs_obj,
            )

            exec_dict = data.get("execution_metadata", {})
            exec_metadata = ExecutionMetadata(
                started_at=str(exec_dict.get("started_at", "")),
                finished_at=str(exec_dict.get("finished_at", "")),
                total_duration_seconds=float(exec_dict.get("total_duration_seconds", 0.0)),
                environment=dict(exec_dict.get("environment", {})),
            )

            checks = [
                CheckSummary(
                    name=str(c.get("name", "")),
                    status=str(c.get("status", "PASSED" if c.get("passed", True) else "FAILED")),
                    passed=bool(c.get("passed", c.get("status") == "PASSED")),
                    exit_code=int(c.get("exit_code", 0)),
                    duration_seconds=float(c.get("duration_seconds", 0.0)),
                    optional=bool(c.get("optional", False)),
                    log_digest=str(c.get("log_digest", "")),
                )
                for c in data.get("checks", [])
            ]

            return VerificationReport(
                schema_version=str(data.get("schema_version", "2.0.0")),
                execution_origin=str(data.get("execution_origin", "LOCAL")),
                verdict=str(data.get("verdict", "PASSED")),
                task_contract=task_contract,
                workspace_state=workspace_state,
                execution_metadata=exec_metadata,
                checks=checks,
            )

        # Legacy fallback conversion
        checks = [
            CheckSummary(
                name=str(c.get("name", "")),
                status="PASSED" if c.get("passed", False) else "FAILED",
                passed=bool(c.get("passed", False)),
                exit_code=int(c.get("exit_code", 0)),
                duration_seconds=float(c.get("duration_seconds", 0.0)),
            )
            for c in data.get("checks", [])
        ]
        return VerificationReport(
            schema_version="1.0.0",
            execution_origin="LOCAL",
            verdict=str(data.get("status", "PASSED")),
            task_contract=TaskContract(
                task_id=str(data.get("task_id", "")),
                task_title=str(data.get("task_title", "")),
                acceptance_criteria=list(data.get("acceptance_criteria", [])),
                unresolved_criteria=list(data.get("unresolved_criteria", [])),
            ),
            workspace_state=WorkspaceState(
                source_manifest_digest_post=str(data.get("source_tree_hash", "")),
            ),
            checks=checks,
        )

    def classify_evidence_payload(self, json_str: str) -> str:
        """Classify an evidence JSON payload."""
        try:
            data = json.loads(json_str)
        except Exception:
            return "MALFORMED_PAYLOAD"

        if data.get("schema_version") == "2.0.0" or "workspace_state" in data:
            return "LOCAL_UNATTESTED" if data.get("execution_origin") == "LOCAL" else "CI_UNPRIVILEGED"
        if "signature" in data or "source_tree_hash" in data:
            return "LEGACY_UNATTESTED"

        return "UNKNOWN_PAYLOAD"

    def verify_workspace_state_match(self, report: VerificationReport, current_manifest_digest: str) -> bool:
        """Verify that report post-execution manifest matches current workspace state."""
        report_digest = str(report.workspace_state.source_manifest_digest_post or "")
        cur_digest = str(current_manifest_digest or "")
        if not report_digest or not cur_digest:
            return False
        if len(cur_digest) == 16 and len(report_digest) > 16:
            report_digest = report_digest[:16]
        elif len(report_digest) == 16 and len(cur_digest) > 16:
            cur_digest = cur_digest[:16]
        return hmac.compare_digest(report_digest, cur_digest)

    def generate_report_markdown(
        self,
        report: VerificationReport,
        title: str = "Verification Report",
    ) -> str:
        """Render verification report as human-readable markdown summary."""
        vcs_head = report.workspace_state.vcs.head if report.workspace_state.vcs else "(no git)"
        vcs_commit = report.workspace_state.vcs.commit if report.workspace_state.vcs else "(no git)"

        lines = [
            f"# {title}",
            "",
            f"**Task ID**: `{report.task_contract.task_id or 'default-run'}`  ",
        ]
        if report.task_contract.task_title:
            lines.append(f"**Task Title**: {report.task_contract.task_title}  ")

        manifest_digest = report.workspace_state.source_manifest_digest_post or "(none)"
        lines.extend(
            [
                f"**Verdict**: `{report.verdict}`  ",
                f"**Execution Origin**: `{report.execution_origin}`  ",
                f"**Source Manifest Digest**: `{manifest_digest}`  ",
                f"**Timestamp**: `{report.execution_metadata.finished_at or 'N/A'}`  ",
                f"**Head**: `{vcs_head}`  ",
                f"**Commit**: `{vcs_commit}`  ",
            ]
        )

        if report.task_contract.acceptance_criteria:
            lines.extend(["", "## Acceptance Criteria", ""])
            for crit in report.task_contract.acceptance_criteria:
                status_icon = "[x]" if crit not in report.task_contract.unresolved_criteria else "[ ]"
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
        for c in report.checks:
            lines.append(f"| `{c.name}` | `{c.status}` | `{c.exit_code}` | `{c.duration_seconds:.3f}s` |")

        lines.extend(["", "---", ""])
        return "\n".join(lines)
