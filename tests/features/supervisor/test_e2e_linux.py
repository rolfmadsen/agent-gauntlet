"""End-to-End integration test simulating complete local supervisor lifecycle on Linux."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.adapters.antigravity.shim import AntigravityHookShim
from agent_gauntlet.features.supervisor.core.engine import SupervisorEngine
from agent_gauntlet.features.supervisor.core.offline_verifier import (
    OfflineReportVerifier,
    SupervisedReportPayload,
)
from agent_gauntlet.features.supervisor.core.snapshot import generate_canonical_snapshot
from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider


class MockIpcTransport:
    def __init__(self, engine: SupervisorEngine) -> None:
        self.engine = engine

    def get_socket_endpoint(self) -> str:
        return "mock://supervisor"

    def send_rpc(self, request, timeout_seconds=2.0):
        return self.engine.handle_rpc(request)


class TestLinuxSupervisorE2E(unittest.TestCase):
    """Verifies complete end-to-end flow: workspace registration -> hook evaluation -> canonical snapshot -> signed report -> offline verification."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp_dir.name)

        # Structure workspace
        (self.workspace / "tasks").mkdir()
        (self.workspace / "tasks" / "035-test.md").write_text("# Task 035", encoding="utf-8")
        (self.workspace / "src").mkdir()
        (self.workspace / "src" / "main.py").write_text("def run(): pass\n", encoding="utf-8")

        self.key_dir = self.workspace / ".keys"
        self.key_provider = LinuxKeyProvider(key_storage_dir=self.key_dir)
        self.engine = SupervisorEngine(key_provider=self.key_provider)
        self.transport = MockIpcTransport(self.engine)
        self.shim = AntigravityHookShim(transport=self.transport)
        self.offline_verifier = OfflineReportVerifier()

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_complete_e2e_lifecycle(self) -> None:
        """Executes full lifecycle from tool hook evaluation to report verification."""
        # 1. Register workspace and start session
        self.engine.register_workspace(str(self.workspace), "ws-e2e")
        session, cert = self.engine.begin_or_resume_session("ws-e2e", "035-test")
        self.assertEqual(session.task_id, "035-test")
        self.assertTrue(cert.task_public_key)

        # 2. Hook evaluation: writing to code under active task is allowed
        hook_payload = {
            "conversationId": "conv-e2e",
            "workspacePaths": [str(self.workspace)],
            "stepIdx": 1,
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "src/main.py", "CodeContent": "def run(): return 42\n"},
            },
        }
        hook_res = self.shim.handle_hook(hook_payload, workspace_id="ws-e2e")
        self.assertEqual(hook_res["decision"], "allow")

        # 3. Generate snapshot
        snapshot = generate_canonical_snapshot(self.workspace)
        self.assertTrue(snapshot.root_digest.startswith("sha256:"))

        # 4. Construct and sign canonical report
        report_data = {
            "schema_version": "3.0.0",
            "assurance_class": "LOCAL_SUPERVISED",
            "verdict": "PASSED",
            "workspace_state": {
                "source_manifest_digest": snapshot.root_digest,
                "task_digest": cert.task_digest,
                "wasm_digest": cert.wasm_digest,
            },
            "event_log_root": self.engine._event_logs[session.session_id].get_root_hash(),
            "task_certificate": cert.to_dict(),
        }
        canonical_bytes = json.dumps(report_data, sort_keys=True).encode("utf-8")
        signature = self.key_provider.sign_canonical_report(canonical_bytes, task_id="035-test")

        payload = SupervisedReportPayload(
            report_data=report_data,
            signature=signature,
        )

        # 5. Offline verification
        verif_result = self.offline_verifier.verify(payload, self.key_provider)
        self.assertTrue(verif_result.is_valid)
        self.assertEqual(verif_result.assurance_class, "LOCAL_SUPERVISED")


if __name__ == "__main__":
    unittest.main()
