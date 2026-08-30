"""Tests for Linux systemd socket activation, unit file templates, and service lifecycle."""

import os
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.supervisor.platform.linux.service import (
    SD_LISTEN_FDS_START,
    SystemdServiceManager,
)


class TestSystemdServiceManager(unittest.TestCase):
    """Verifies that SystemdServiceManager generates correct unit files and detects socket activation."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.unit_dir = Path(self.tmp_dir.name)
        self.manager = SystemdServiceManager(unit_dir=self.unit_dir)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_unit_file_generation(self) -> None:
        """Generates valid agent-gauntlet.socket and agent-gauntlet.service files."""
        socket_file, service_file = self.manager.generate_unit_files(
            exec_start_path="/usr/local/bin/agent-gauntlet-supervisor",
            socket_path="/run/user/1000/agent-gauntlet/supervisor.sock",
        )
        self.assertTrue(socket_file.is_file())
        self.assertTrue(service_file.is_file())

        socket_content = socket_file.read_text(encoding="utf-8")
        self.assertIn("ListenStream=/run/user/1000/agent-gauntlet/supervisor.sock", socket_content)
        self.assertIn("SocketMode=0600", socket_content)

        service_content = service_file.read_text(encoding="utf-8")
        self.assertIn("ExecStart=/usr/local/bin/agent-gauntlet-supervisor", service_content)
        self.assertIn("Requires=agent-gauntlet.socket", service_content)

    def test_socket_activation_detection_from_environment(self) -> None:
        """Detects socket activation when LISTEN_FDS and LISTEN_PID match current process."""
        pid = str(os.getpid())
        os.environ["LISTEN_PID"] = pid
        os.environ["LISTEN_FDS"] = "2"
        try:
            self.assertTrue(self.manager.is_socket_activated())
            fds = self.manager.get_socket_file_descriptors()
            self.assertEqual(fds, [SD_LISTEN_FDS_START, SD_LISTEN_FDS_START + 1])
        finally:
            os.environ.pop("LISTEN_PID", None)
            os.environ.pop("LISTEN_FDS", None)

    def test_socket_activation_false_when_unmatched(self) -> None:
        """Returns False when LISTEN_PID or LISTEN_FDS are missing or unmatched."""
        os.environ.pop("LISTEN_PID", None)
        os.environ.pop("LISTEN_FDS", None)
        self.assertFalse(self.manager.is_socket_activated())
        self.assertEqual(self.manager.get_socket_file_descriptors(), [])


if __name__ == "__main__":
    unittest.main()
