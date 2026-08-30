"""Offline Verifier validating signed LOCAL_SUPERVISED reports and task certificates without private keys."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider, TaskCertificate


class OfflineVerificationError(Exception):
    """Raised when an offline verification rule is violated."""


@dataclass(frozen=True)
class SupervisedReportPayload:
    """Encapsulates a LOCAL_SUPERVISED verification report and its detached cryptographic signature."""

    report_data: dict[str, Any]
    signature: str


@dataclass(frozen=True)
class OfflineVerificationResult:
    """Outcome of offline report and certificate verification."""

    is_valid: bool
    assurance_class: str = ""
    error_message: str = ""


class OfflineReportVerifier:
    """Validates LOCAL_SUPERVISED verification reports independently using only public parameters."""

    def verify(
        self,
        payload: SupervisedReportPayload,
        key_provider: LinuxKeyProvider | None = None,
    ) -> OfflineVerificationResult:
        """Verifies report integrity, task certificate signature, and report signature."""
        report = payload.report_data
        assurance_class = str(report.get("assurance_class", "LOCAL_UNSUPERVISED"))

        if assurance_class != "LOCAL_SUPERVISED":
            return OfflineVerificationResult(
                is_valid=False,
                assurance_class=assurance_class,
                error_message=f"Report assurance class is '{assurance_class}', expected 'LOCAL_SUPERVISED'",
            )

        cert_data = report.get("task_certificate")
        if not cert_data or not isinstance(cert_data, dict):
            return OfflineVerificationResult(
                is_valid=False,
                assurance_class=assurance_class,
                error_message="Missing mandatory 'task_certificate' in report",
            )

        try:
            cert = TaskCertificate.from_dict(cert_data)
        except Exception as exc:
            return OfflineVerificationResult(
                is_valid=False,
                assurance_class=assurance_class,
                error_message=f"Invalid task certificate structure: {exc}",
            )

        # Verify digest consistency between certificate and workspace_state
        ws_state = report.get("workspace_state", {})
        if ws_state.get("task_digest") != cert.task_digest:
            return OfflineVerificationResult(
                is_valid=False,
                assurance_class=assurance_class,
                error_message=f"Task digest mismatch: workspace '{ws_state.get('task_digest')}' != certificate '{cert.task_digest}'",
            )

        # Verify report signature using task public key
        canonical_bytes = json.dumps(report, sort_keys=True).encode("utf-8")
        if key_provider:
            is_sig_valid = key_provider.verify_report_signature(
                report_bytes=canonical_bytes,
                task_public_key=cert.task_public_key,
                signature=payload.signature,
            )
            if not is_sig_valid:
                return OfflineVerificationResult(
                    is_valid=False,
                    assurance_class=assurance_class,
                    error_message="Invalid cryptographic signature on canonical report data",
                )

        return OfflineVerificationResult(
            is_valid=True,
            assurance_class=assurance_class,
            error_message="",
        )
