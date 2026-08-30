"""Tests for Protected Key Provider, ephemeral task keys, certificates, and canonical signing."""

import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.platform.linux.keys import (
    LinuxKeyProvider,
)


class TestLinuxKeyProvider(unittest.TestCase):
    """Verifies that LinuxKeyProvider manages installation identity and ephemeral task keys with strict permissions."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.key_dir = Path(self.tmp_dir.name)
        self.provider = LinuxKeyProvider(key_storage_dir=self.key_dir)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_installation_identity_generation_and_persistence(self) -> None:
        """Installation public key is generated and persisted across provider reloads."""
        pub_key1 = self.provider.get_installation_public_key()
        self.assertTrue(pub_key1.startswith("ag_inst_"))

        # Reload from same directory
        reloaded = LinuxKeyProvider(key_storage_dir=self.key_dir)
        pub_key2 = reloaded.get_installation_public_key()
        self.assertEqual(pub_key1, pub_key2)

    def test_ephemeral_task_key_and_certificate_issuance(self) -> None:
        """Generates an ephemeral task key and issues a verifiable task certificate."""
        cert = self.provider.issue_task_certificate(
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:taskdigest123",
            wasm_digest="sha256:wasmdigest456",
        )
        self.assertEqual(cert.task_id, "035-supervisor")
        self.assertEqual(cert.workspace_id, "ws-abc")
        self.assertEqual(cert.installation_public_key, self.provider.get_installation_public_key())
        self.assertTrue(cert.task_public_key.startswith("ag_task_"))
        self.assertTrue(cert.certificate_signature)

        # Validate certificate signature against installation public key
        self.assertTrue(self.provider.verify_task_certificate(cert))

    def test_canonical_report_signing_and_verification(self) -> None:
        """Signs canonical report payload with ephemeral task key and verifies signature."""
        cert = self.provider.issue_task_certificate(
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:task123",
            wasm_digest="sha256:wasm456",
        )
        report_bytes = b'{"verdict": "PASSED", "workspace_digest": "sha256:ws999"}'
        signature = self.provider.sign_canonical_report(
            report_bytes=report_bytes,
            task_id="035-supervisor",
        )
        self.assertTrue(signature.startswith("sig_"))

        # Verify signature with public task key
        self.assertTrue(
            self.provider.verify_report_signature(
                report_bytes=report_bytes,
                task_public_key=cert.task_public_key,
                signature=signature,
            )
        )

        # Tampered payload fails verification
        tampered = b'{"verdict": "PASSED", "workspace_digest": "sha256:TAMPERED"}'
        self.assertFalse(
            self.provider.verify_report_signature(
                report_bytes=tampered,
                task_public_key=cert.task_public_key,
                signature=signature,
            )
        )


if __name__ == "__main__":
    unittest.main()
