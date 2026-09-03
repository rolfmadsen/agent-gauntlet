"""Unix Domain Socket server for local supervisor daemon with systemd socket activation."""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
from pathlib import Path
from types import TracebackType

from agent_gauntlet.features.supervisor.core.engine import SupervisorEngine
from agent_gauntlet.features.supervisor.core.models import RpcRequest, RpcResponse
from agent_gauntlet.features.supervisor.platform.linux.service import SystemdServiceManager

logger = logging.getLogger(__name__)


class SupervisorServer:
    """Listens on a Unix domain socket and dispatches RPC requests line-by-line."""

    def __init__(
        self,
        engine: SupervisorEngine | None = None,
        socket_path: Path | str | None = None,
        systemd_manager: SystemdServiceManager | None = None,
    ) -> None:
        self.engine = engine or SupervisorEngine()
        self.systemd_manager = systemd_manager or SystemdServiceManager()

        if socket_path:
            self.socket_path = Path(socket_path).resolve()
        else:
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
            if runtime_dir:
                base = Path(runtime_dir) / "agent-gauntlet"
            else:
                base = Path.home() / ".local" / "state" / "agent-gauntlet"
            self.socket_path = (base / "supervisor.sock").resolve()

        self._server_sock: socket.socket | None = None
        self._is_socket_activated: bool = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._client_threads: list[threading.Thread] = []
        self._is_running: bool = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Returns True if the server is currently bound and serving."""
        return self._is_running

    def _setup_socket(self) -> socket.socket:
        """Configures or inherits the server socket."""
        if self.systemd_manager.is_socket_activated():
            fds = self.systemd_manager.get_socket_file_descriptors()
            if fds:
                sock = socket.fromfd(fds[0], socket.AF_UNIX, socket.SOCK_STREAM)
                sock.setblocking(False)
                self._is_socket_activated = True
                return sock

        # Standalone socket setup
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(str(self.socket_path))
        try:
            os.chmod(str(self.socket_path), 0o600)
        except OSError:
            pass
        sock.listen(128)
        sock.settimeout(0.5)
        self._is_socket_activated = False
        return sock

    def _handle_client(self, client_sock: socket.socket) -> None:
        """Reads newline-delimited JSON-RPC requests, evaluates, and writes back responses."""
        client_sock.settimeout(10.0)
        buffer = b""
        try:
            while not self._stop_event.is_set():
                try:
                    chunk = client_sock.recv(4096)
                except (socket.timeout, TimeoutError):
                    continue
                except OSError:
                    break

                if not chunk:
                    break

                buffer += chunk
                while b"\n" in buffer:
                    line_bytes, buffer = buffer.split(b"\n", 1)
                    line_str = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line_str:
                        continue

                    try:
                        rpc_req = RpcRequest.from_json(line_str)
                        rpc_res = self.engine.handle_rpc(rpc_req)
                    except Exception as exc:
                        rpc_res = RpcResponse(
                            id="unknown",
                            error={"code": -32700, "message": f"Parse or dispatch error: {exc}"},
                        )

                    payload = (rpc_res.to_json() + "\n").encode("utf-8")
                    try:
                        client_sock.sendall(payload)
                    except OSError:
                        return
        finally:
            try:
                client_sock.close()
            except OSError:
                pass

    def serve_forever(self) -> None:
        """Main blocking accept loop."""
        with self._lock:
            if self._is_running:
                return
            self._server_sock = self._setup_socket()
            self._is_running = True
            self._stop_event.clear()

        try:
            while not self._stop_event.is_set():
                if self._server_sock is None:
                    break
                try:
                    conn, _ = self._server_sock.accept()
                except (socket.timeout, TimeoutError):
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    continue

                t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                t.start()
                with self._lock:
                    self._client_threads = [th for th in self._client_threads if th.is_alive()]
                    self._client_threads.append(t)
        finally:
            self._cleanup()

    def start(self) -> None:
        """Starts the server loop in a background daemon thread."""
        with self._lock:
            if self._is_running:
                return
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()
        # Wait until socket is ready
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if self._is_running and (self._is_socket_activated or self.socket_path.exists()):
                break
            time.sleep(0.01)

    def stop(self) -> None:
        """Signals server to stop and releases socket resources."""
        self._stop_event.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
            self._server_sock = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

        self._cleanup()

    def _cleanup(self) -> None:
        """Cleans up sockets and files."""
        with self._lock:
            self._is_running = False
        if not self._is_socket_activated and self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass

    def __enter__(self) -> SupervisorServer:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()
