"""Linux systemd service and socket activation integration."""

from __future__ import annotations

import os
from pathlib import Path

from agent_gauntlet.features.supervisor.core.seams import ServiceLifecycleSeam

SD_LISTEN_FDS_START = 3


class SystemdServiceManager(ServiceLifecycleSeam):
    """Manages systemd socket and service units for the agent-gauntlet supervisor daemon."""

    def __init__(self, unit_dir: Path | None = None) -> None:
        if unit_dir:
            self.unit_dir = Path(unit_dir).resolve()
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
            self.unit_dir = (base / "systemd" / "user").resolve()

    def generate_unit_files(
        self,
        exec_start_path: str,
        socket_path: str,
    ) -> tuple[Path, Path]:
        """Generates agent-gauntlet.socket and agent-gauntlet.service unit files."""
        self.unit_dir.mkdir(parents=True, exist_ok=True)

        socket_file = self.unit_dir / "agent-gauntlet.socket"
        socket_content = f"""[Unit]
Description=agent-gauntlet Local Supervisor Socket Activation
Documentation=https://github.com/rolfmadsen/agent-gauntlet

[Socket]
ListenStream={socket_path}
SocketMode=0600
Accept=false

[Install]
WantedBy=sockets.target
"""
        socket_file.write_text(socket_content, encoding="utf-8")

        service_file = self.unit_dir / "agent-gauntlet.service"
        service_content = f"""[Unit]
Description=agent-gauntlet Local Supervisor Daemon
Documentation=https://github.com/rolfmadsen/agent-gauntlet
Requires=agent-gauntlet.socket
After=agent-gauntlet.socket

[Service]
ExecStart={exec_start_path}
NonBlocking=true
NoNewPrivileges=yes
ProtectSystem=strict
PrivateTmp=yes
Restart=on-failure

[Install]
WantedBy=default.target
"""
        service_file.write_text(service_content, encoding="utf-8")

        return socket_file, service_file

    def is_socket_activated(self) -> bool:
        """Returns True if the current process was activated by systemd socket activation."""
        listen_pid_str = os.environ.get("LISTEN_PID")
        listen_fds_str = os.environ.get("LISTEN_FDS")

        if not listen_pid_str or not listen_fds_str:
            return False

        try:
            listen_pid = int(listen_pid_str)
            listen_fds = int(listen_fds_str)
            return listen_pid == os.getpid() and listen_fds >= 1
        except ValueError:
            return False

    def get_socket_file_descriptors(self) -> list[int]:
        """Returns list of open file descriptors passed by systemd starting from SD_LISTEN_FDS_START."""
        if not self.is_socket_activated():
            return []

        count = int(os.environ.get("LISTEN_FDS", "0"))
        return [SD_LISTEN_FDS_START + i for i in range(count)]
