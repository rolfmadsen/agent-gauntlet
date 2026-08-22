"""HMAC-signed evidence ledger and evidence generator for agent-gauntlet."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

from agent_gauntlet.features.evidence.models import CheckSummary, EvidenceRecord


class EvidenceAuthority:
    """Authority for cryptographically signing, verifying, and rendering evidence ledgers."""

    DEFAULT_KEY: bytes = b"agent-gauntlet-default-authority-key-v1"

    def __init__(self, secret_key: bytes | str | None = None) -> None:
        if secret_key is None:
            self._key = self.DEFAULT_KEY
        elif isinstance(secret_key, str):
            self._key = secret_key.encode("utf-8")
        else:
            self._key = secret_key

    def _canonical_payload(self, record: EvidenceRecord) -> bytes:
        """Produce deterministic canonical JSON payload for HMAC signing."""
        sorted_checks = [
            {
                "duration_seconds": round(c.duration_seconds, 6),
                "exit_code": int(c.exit_code),
                "name": str(c.name),
                "passed": bool(c.passed),
            }
            for c in record.checks
        ]
        payload_dict = {
            "acceptance_criteria": sorted(list(record.acceptance_criteria)),
            "checks": sorted_checks,
            "source_tree_hash": str(record.source_tree_hash),
            "status": str(record.status),
            "task_id": str(record.task_id),
            "task_title": str(record.task_title),
            "timestamp": round(float(record.timestamp), 6),
            "unresolved_criteria": sorted(list(record.unresolved_criteria)),
        }
        return json.dumps(payload_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def sign_record(self, record: EvidenceRecord) -> EvidenceRecord:
        """Sign record payload using HMAC-SHA256."""
        payload = self._canonical_payload(record)
        signature = hmac.new(self._key, payload, hashlib.sha256).hexdigest()
        return EvidenceRecord(
            task_id=record.task_id,
            status=record.status,
            source_tree_hash=record.source_tree_hash,
            task_title=record.task_title,
            acceptance_criteria=list(record.acceptance_criteria),
            unresolved_criteria=list(record.unresolved_criteria),
            checks=list(record.checks),
            timestamp=record.timestamp,
            signature=signature,
        )

    def verify_record(self, record: EvidenceRecord) -> bool:
        """Verify HMAC signature against canonical payload."""
        if not record.signature or not isinstance(record.signature, str):
            return False

        payload = self._canonical_payload(record)
        expected_signature = hmac.new(self._key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(record.signature, expected_signature)

    def verify_source_state_match(self, record: EvidenceRecord, current_tree_hash: str) -> bool:
        """Verify that record signature is valid AND source tree hash matches current workspace."""
        if not self.verify_record(record):
            return False
        return hmac.compare_digest(record.source_tree_hash, str(current_tree_hash))

    def generate_evidence_json(self, record: EvidenceRecord) -> str:
        """Serialize evidence record to formatted JSON."""
        data = {
            "task_id": record.task_id,
            "task_title": record.task_title,
            "status": record.status,
            "source_tree_hash": record.source_tree_hash,
            "timestamp": record.timestamp,
            "signature": record.signature,
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
                passed=bool(c["passed"]),
                exit_code=int(c["exit_code"]),
                duration_seconds=float(c.get("duration_seconds", 0.0)),
            )
            for c in data.get("checks", [])
        ]
        return EvidenceRecord(
            task_id=str(data.get("task_id", "")),
            task_title=str(data.get("task_title", "")),
            status=str(data.get("status", "")),
            source_tree_hash=str(data.get("source_tree_hash", "")),
            acceptance_criteria=list(data.get("acceptance_criteria", [])),
            unresolved_criteria=list(data.get("unresolved_criteria", [])),
            checks=checks,
            timestamp=float(data.get("timestamp", 0.0)),
            signature=data.get("signature"),
        )

    def generate_evidence_markdown(
        self,
        record: EvidenceRecord,
        head: str = "(no git)",
        source_commit: str = "(no git)",
        title: str = "Evidence Report",
    ) -> str:
        """Render evidence record as markdown report."""
        iso_time = (
            datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if record.timestamp > 0
            else "N/A"
        )
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
                f"**Signature**: `{record.signature or 'UNSIGNED'}`  ",
                f"**Timestamp**: `{iso_time}`  ",
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
            verdict = "PASSED" if c.passed else "FAILED"
            lines.append(f"| `{c.name}` | `{verdict}` | `{c.exit_code}` | `{c.duration_seconds:.3f}s` |")

        lines.extend(["", "---", ""])
        return "\n".join(lines)
