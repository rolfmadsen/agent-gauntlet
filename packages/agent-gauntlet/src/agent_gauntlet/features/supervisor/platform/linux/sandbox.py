"""Linux Bubblewrap and isolated process sandbox runner implementation."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import time
from pathlib import Path

from agent_gauntlet.features.supervisor.core.seams import (
    SandboxExecutionResult,
    SandboxExecutionSpec,
    SandboxRunnerSeam,
)


class BubblewrapSandboxRunner(SandboxRunnerSeam):
    """Executes verification and check commands inside unprivileged Linux namespaces or isolated subprocesses."""

    def __init__(self, bwrap_bin: str | None = None, force_fallback: bool = False) -> None:
        self.bwrap_bin = None if force_fallback else (bwrap_bin or shutil.which("bwrap"))
        self._is_bwrap_functional = False

        if self.bwrap_bin and Path(self.bwrap_bin).is_file():
            # Probe if kernel permits nested namespaces in this environment
            try:
                probe = subprocess.run(
                    [self.bwrap_bin, "--ro-bind", "/", "/", "true"],
                    capture_output=True,
                    timeout=1.0,
                )
                self._is_bwrap_functional = probe.returncode == 0
            except Exception:
                self._is_bwrap_functional = False

    @property
    def is_bwrap_available(self) -> bool:
        """Returns True if Bubblewrap is installed and functional on the host kernel."""
        return self._is_bwrap_functional

    def execute(self, spec: SandboxExecutionSpec) -> SandboxExecutionResult:
        """Executes a command within an isolated environment.

        If bwrap is functional, uses Linux user namespaces with unshared network.
        Otherwise uses clean isolated subprocess execution.
        """
        start_time = time.monotonic()

        if self._is_bwrap_functional and self.bwrap_bin:
            cmd = [
                self.bwrap_bin,
                "--unshare-pid",
                "--unshare-ipc",
                "--unshare-uts",
            ]
            if not spec.network_enabled:
                cmd.append("--unshare-net")

            # Mount host system roots read-only
            for sys_dir in ("/usr", "/lib", "/lib64", "/bin", "/etc"):
                if Path(sys_dir).exists():
                    cmd.extend(["--ro-bind", sys_dir, sys_dir])

            # Mount workspace snapshot or cwd
            target_ws = spec.snapshot_dir or spec.cwd
            if spec.read_only_root:
                cmd.extend(["--ro-bind", target_ws, target_ws])
            else:
                cmd.extend(["--bind", target_ws, target_ws])

            cmd.extend(
                [
                    "--tmpfs",
                    "/tmp",
                    "--proc",
                    "/proc",
                    "--dev",
                    "/dev",
                    "--chdir",
                    spec.cwd,
                    "--die-with-parent",
                    "--",
                    spec.program,
                    *spec.args,
                ]
            )
        else:
            cmd = [spec.program, *spec.args]

        env = dict(spec.env) if spec.env else None
        timed_out = False
        exit_code = 0
        stdout_str = ""
        stderr_str = ""

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=spec.cwd,
                env=env,
                timeout=spec.timeout_seconds,
            )
            exit_code = proc.returncode
            stdout_str = proc.stdout
            stderr_str = proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = 124
            stdout_str = exc.stdout or "" if isinstance(exc.stdout, str) else ""
            stderr_str = exc.stderr or "" if isinstance(exc.stderr, str) else ""
        except Exception as exc:
            exit_code = 127
            stderr_str = str(exc)

        duration = time.monotonic() - start_time
        stdout_digest = f"sha256:{hashlib.sha256(stdout_str.encode('utf-8')).hexdigest()}"
        stderr_digest = f"sha256:{hashlib.sha256(stderr_str.encode('utf-8')).hexdigest()}"

        return SandboxExecutionResult(
            exit_code=exit_code,
            stdout=stdout_str,
            stderr=stderr_str,
            duration_seconds=duration,
            timed_out=timed_out,
            stdout_digest=stdout_digest,
            stderr_digest=stderr_digest,
        )
