"""Tests for Offline Verifier, certifying LOCAL_SUPERVISED reports without private keys."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.core.offline_verifier import (
    OfflineReportVerifier,
    SupervisedReportPayload,
)
from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider


class TestOfflineReportVerifier(unittest.TestCase):
    """Verifies that OfflineReportVerifier validates signed LOCAL_SUPERVISED reports without private keys."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.key_dir = Path(self.tmp_dir.name)
        self.key_provider = LinuxKeyProvider(key_storage_dir=self.key_dir)
        self.offline_verifier = OfflineReportVerifier()

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_valid_supervised_report_passes_offline_verification(self) -> None:
        """A properly signed LOCAL_SUPERVISED report with valid task certificate passes verification."""
        cert = self.key_provider.issue_task_certificate(
            workspace_id="ws-1",
            task_id="035-supervisor",
            task_digest="sha256:taskdigest",
            wasm_digest="sha256:wasmdigest",
        )
        report_data = {
            "schema_version": "3.0.0",
            "assurance_class": "LOCAL_SUPERVISED",
            "verdict": "PASSED",
            "workspace_state": {
                "source_manifest_digest": "sha256:manifest123",
                "task_digest": "sha256:taskdigest",
                "wasm_digest": "sha256:wasmdigest",
            },
            "event_log_root": "sha256:eventroot789",
            "task_certificate": cert.to_dict(),
        }
        canonical_bytes = json.dumps(report_data, sort_keys=True).encode("utf-8")
        signature = self.key_provider.sign_canonical_report(
            canonical_bytes, task_id="035-supervisor"
        )

        supervised_payload = SupervisedReportPayload(
            report_data=report_data,
            signature=signature,
        )

        res = self.offline_verifier.verify(supervised_payload, self.key_provider)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.assurance_class, "LOCAL_SUPERVISED")

    def test_tampered_report_data_rejected_fail_closed(self) -> None:
        """Tampering with report data causes signature verification failure."""
        cert = self.key_provider.issue_task_certificate(
            workspace_id="ws-1",
            task_id="035-supervisor",
            task_digest="sha256:taskdigest",
            wasm_digest="sha256:wasmdigest",
        )
        report_data = {
            "schema_version": "3.0.0",
            "assurance_class": "LOCAL_SUPERVISED",
            "verdict": "PASSED",
            "workspace_state": {"task_digest": "sha256:taskdigest"},
            "task_certificate": cert.to_dict(),
        }
        canonical_bytes = json.dumps(report_data, sort_keys=True).encode("utf-8")
        signature = self.key_provider.sign_canonical_report(
            canonical_bytes, task_id="035-supervisor"
        )

        # Tamper with verdict
        report_data["verdict"] = "FAILED"
        tampered_payload = SupervisedReportPayload(
            report_data=report_data,
            signature=signature,
        )

        res = self.offline_verifier.verify(tampered_payload, self.key_provider)
        self.assertFalse(res.is_valid)
        self.assertIn("signature", res.error_message.lower())


if __name__ == "__main__":
    unittest.main()
