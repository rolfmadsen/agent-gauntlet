"""Narrow, decoupled platform seams isolating OS-specific implementations from the supervisor core."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


class UnsupportedPlatformError(Exception):
    """Raised when an operation is requested on a platform without native seam support."""


@dataclass(frozen=True)
class SandboxExecutionSpec:
    """Declarative specification for isolated command execution in a sandbox."""

    program: str
    args: list[str]
    cwd: str
    snapshot_dir: str
    env: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 60.0
    network_enabled: bool = False
    read_only_root: bool = True


@dataclass(frozen=True)
class SandboxExecutionResult:
    """Structured result returned by a sandbox runner execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    stdout_digest: str = ""
    stderr_digest: str = ""


@runtime_checkable
class ServiceLifecycleSeam(Protocol):
    """Lifecycle and socket activation contract for the supervisor daemon."""

    def is_socket_activated(self) -> bool:
        """Returns True if the current process was activated via socket activation."""
        ...

    def get_socket_file_descriptors(self) -> list[int]:
        """Returns the list of open socket file descriptors provided by the service manager."""
        ...


@runtime_checkable
class IpcTransportSeam(Protocol):
    """Local IPC transport contract for daemon-client communication."""

    def get_socket_endpoint(self) -> str:
        """Returns the canonical platform IPC endpoint path or address."""
        ...

    def send_rpc(self, request: Any, timeout_seconds: float = 2.0) -> Any:
        """Sends a JSON-RPC request and returns the parsed response."""
        ...


@runtime_checkable
class SandboxRunnerSeam(Protocol):
    """Isolated unprivileged command runner contract."""

    def execute(self, spec: SandboxExecutionSpec) -> SandboxExecutionResult:
        """Executes a command within an unprivileged sandbox matching the specification."""
        ...


@runtime_checkable
class KeyProviderSeam(Protocol):
    """OS-protected cryptographic key provider contract."""

    def get_installation_public_key(self) -> str:
        """Returns the persistent installation public key identifier."""
        ...

    def create_ephemeral_task_key(self, task_id: str) -> str:
        """Generates an ephemeral task key and returns the public task key certificate."""
        ...

    def sign_payload(self, payload: bytes, task_id: str) -> str:
        """Signs a canonical payload using the task ephemeral private key."""
        ...


@runtime_checkable
class PlatformPathsSeam(Protocol):
    """Platform-specific directory and permission conventions contract."""

    def get_runtime_dir(self) -> Path:
        """Returns the platform directory for ephemeral runtime sockets."""
        ...

    def get_data_dir(self) -> Path:
        """Returns the platform directory for persistent supervisor state."""
        ...


def get_platform_name() -> str:
    """Returns the normalized platform name."""
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform in ("win32", "cygwin"):
        return "windows"
    return sys.platform


def get_platform_seam(platform_name: str | None = None) -> str:
    """Validates platform support and returns the registered platform driver name.

    Raises:
        UnsupportedPlatformError: If the platform is not Linux (or planned macOS/Windows before implementation).
    """
    target = platform_name or get_platform_name()
    if target == "linux":
        return "linux"
    raise UnsupportedPlatformError(
        f"Platform '{target}' is currently unsupported for LOCAL_SUPERVISED mode. "
        "Native supervisor support is currently implemented for Linux (systemd & bubblewrap). "
        "macOS and Windows support is planned (Tasks 036 & 037)."
    )
