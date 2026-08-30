"""Unix Domain Socket IPC transport for local supervisor daemon and client."""

from __future__ import annotations

import os
import socket
from pathlib import Path

from agent_gauntlet.features.supervisor.core.models import RpcRequest, RpcResponse
from agent_gauntlet.features.supervisor.core.seams import IpcTransportSeam


class UnixDomainSocketTransport(IpcTransportSeam):
    """Handles IPC message exchange over UNIX domain sockets."""

    def __init__(self, socket_path: Path | None = None) -> None:
        if socket_path:
            self.socket_path = Path(socket_path).resolve()
        else:
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
            if runtime_dir:
                base = Path(runtime_dir) / "agent-gauntlet"
            else:
                base = Path.home() / ".local" / "state" / "agent-gauntlet"
            self.socket_path = (base / "supervisor.sock").resolve()

    def get_socket_endpoint(self) -> str:
        """Returns the canonical UNIX socket path."""
        return str(self.socket_path)

    def send_rpc(self, request: RpcRequest, timeout_seconds: float = 2.0) -> RpcResponse:
        """Connects to supervisor daemon socket, sends JSON-RPC request and parses response."""
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.settimeout(timeout_seconds)
        try:
            client_sock.connect(str(self.socket_path))
            payload = (request.to_json() + "\n").encode("utf-8")
            client_sock.sendall(payload)

            response_data = b""
            while True:
                chunk = client_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in response_data:
                    break

            raw_str = response_data.decode("utf-8").strip()
            return RpcResponse.from_json(raw_str)
        finally:
            client_sock.close()
