"""Tests for Unix Domain Socket IPC transport, framed JSON-RPC message exchange."""

import socket
import tempfile
import threading
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.core.models import RpcMethod, RpcRequest, RpcResponse
from agent_gauntlet.features.supervisor.platform.linux.ipc import UnixDomainSocketTransport


class TestUnixDomainSocketTransport(unittest.TestCase):
    """Verifies that UnixDomainSocketTransport sends and receives framed JSON-RPC messages."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.socket_path = Path(self.tmp_dir.name) / "test_supervisor.sock"
        self.transport = UnixDomainSocketTransport(socket_path=self.socket_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_send_and_receive_framed_rpc(self) -> None:
        """Transmits an RPC request over Unix socket and receives matching RPC response."""
        # Simple echo server thread
        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(self.socket_path))
        server_sock.listen(1)

        def server_loop():
            conn, _ = server_sock.accept()
            data = conn.recv(4096).decode("utf-8")
            req = RpcRequest.from_json(data.strip())
            res = RpcResponse(id=req.id, result={"status": "OK", "echo": req.method.value})
            conn.sendall((res.to_json() + "\n").encode("utf-8"))
            conn.close()
            server_sock.close()

        t = threading.Thread(target=server_loop, daemon=True)
        t.start()

        # Client invocation
        req = RpcRequest(id="req-123", method=RpcMethod.GET_STATUS)
        res = self.transport.send_rpc(req)
        t.join(timeout=2.0)

        self.assertTrue(res.is_success)
        self.assertEqual(res.id, "req-123")
        self.assertIsNotNone(res.result)
        assert res.result is not None
        self.assertEqual(res.result["echo"], "GetStatus")


if __name__ == "__main__":
    unittest.main()
