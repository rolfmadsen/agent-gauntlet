"""Tests for Supervisor Unix Domain Socket Server and systemd socket activation."""

import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from agent_gauntlet.features.supervisor.core.engine import SupervisorEngine
from agent_gauntlet.features.supervisor.core.models import (
    CapabilityRequest,
    RpcMethod,
    RpcRequest,
    ToolActionType,
)
from agent_gauntlet.features.supervisor.platform.linux.ipc import UnixDomainSocketTransport
from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider
from agent_gauntlet.features.supervisor.platform.linux.server import SupervisorServer
from agent_gauntlet.features.supervisor.platform.linux.service import SystemdServiceManager


class TestSupervisorServer(unittest.TestCase):
    """Verifies that SupervisorServer accepts connections, serves RPCs, and handles lifecycle."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.socket_path = Path(self.tmp_dir.name) / "supervisor_test.sock"
        self.key_dir = Path(self.tmp_dir.name) / "keys"
        self.key_provider = LinuxKeyProvider(key_storage_dir=self.key_dir)
        self.engine = SupervisorEngine(key_provider=self.key_provider)
        self.server = SupervisorServer(engine=self.engine, socket_path=self.socket_path)
        self.transport = UnixDomainSocketTransport(socket_path=self.socket_path)

    def tearDown(self) -> None:
        if self.server.is_running:
            self.server.stop()
        self.tmp_dir.cleanup()

    def test_server_starts_and_answers_get_status(self) -> None:
        """Starts server in background, sends GetStatus RPC, and receives HEALTHY response."""
        self.server.start()
        self.assertTrue(self.server.is_running)
        self.assertTrue(self.socket_path.exists())

        req = RpcRequest(id="req-status", method=RpcMethod.GET_STATUS)
        res = self.transport.send_rpc(req)
        self.assertTrue(res.is_success)
        self.assertEqual(res.id, "req-status")
        assert res.result is not None
        self.assertEqual(res.result.get("status"), "HEALTHY")

    def test_server_evaluates_tool_call(self) -> None:
        """Evaluates tool call through socket server with real engine."""
        self.server.start()

        # Without active task -> deny
        cap_req = CapabilityRequest(
            action_type=ToolActionType.WRITE_FILE,
            raw_tool_name="write_to_file",
            target_resource="src/main.py",
        )
        rpc_req = RpcRequest(
            id="req-eval",
            method=RpcMethod.EVALUATE_TOOL_CALL,
            params={"workspace_id": "ws-1", "request": cap_req.to_dict()},
        )
        res = self.transport.send_rpc(rpc_req)
        self.assertTrue(res.is_success)
        assert res.result is not None
        dec = res.result.get("decision", {})
        self.assertEqual(dec.get("verdict"), "deny")

        # Start session on workspace
        self.engine.register_workspace(str(self.tmp_dir.name), "ws-1")
        self.engine.begin_or_resume_session("ws-1", "043-task")

        # Now evaluation must be allow
        res_after = self.transport.send_rpc(rpc_req)
        self.assertTrue(res_after.is_success)
        assert res_after.result is not None
        dec_after = res_after.result.get("decision", {})
        self.assertEqual(dec_after.get("verdict"), "allow")

    def test_server_cleanup_removes_socket_file(self) -> None:
        """Stopping the server cleanly unlinks the socket file."""
        self.server.start()
        self.assertTrue(self.socket_path.exists())
        self.server.stop()
        self.assertFalse(self.server.is_running)
        self.assertFalse(self.socket_path.exists())

    def test_server_socket_activation_mode(self) -> None:
        """When systemd socket activation is detected, adopts existing file descriptor."""
        mock_mgr = MagicMock(spec=SystemdServiceManager)
        mock_mgr.is_socket_activated.return_value = True

        # Create a real temporary pair of sockets to simulate systemd passed fd
        parent_sock, child_sock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        mock_mgr.get_socket_file_descriptors.return_value = [parent_sock.fileno()]

        activated_server = SupervisorServer(
            engine=self.engine,
            socket_path=self.socket_path,
            systemd_manager=mock_mgr,
        )
        sock = activated_server._setup_socket()
        self.assertTrue(activated_server._is_socket_activated)
        sock.close()
        parent_sock.close()
        child_sock.close()

    def test_concurrent_rpc_requests(self) -> None:
        """Verifies that multiple threads can send RPCs concurrently without race conditions."""
        import concurrent.futures

        self.server.start()
        self.engine.register_workspace(str(self.tmp_dir.name), "ws-concurrent")
        self.engine.begin_or_resume_session("ws-concurrent", "043-threadsafe")

        def send_call(i: int) -> bool:
            trans = UnixDomainSocketTransport(socket_path=self.socket_path)
            req = RpcRequest(
                id=f"req-{i}",
                method=RpcMethod.EVALUATE_TOOL_CALL,
                params={
                    "workspace_id": "ws-concurrent",
                    "request": {
                        "action_type": "write_file",
                        "raw_tool_name": "write_to_file",
                        "target_resource": f"src/mod_{i}.py",
                    },
                },
            )
            res = trans.send_rpc(req, timeout_seconds=3.0)
            return (
                res.is_success
                and res.result is not None
                and res.result.get("decision", {}).get("verdict") == "allow"
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(send_call, range(20)))

        self.assertEqual(len(results), 20)
        self.assertTrue(all(results))


if __name__ == "__main__":
    unittest.main()
