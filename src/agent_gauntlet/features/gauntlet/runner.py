"""Multi-layer verification runner for agent-gauntlet."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

from agent_gauntlet.features.gauntlet.models import (
    GauntletReport,
    LayerDefinition,
    LayerExecutionStatus,
    LayerRequirement,
    LayerResult,
)


def _execute_layer(
    layer: LayerDefinition,
    cwd: str | Path | None = None,
) -> LayerResult:
    """Execute a single layer command and capture output, exit code and duration."""
    start_time = time.perf_counter()
    req = layer.requirement
    env = dict(os.environ)
    src_dir = Path(cwd or ".").resolve() / "src"
    if src_dir.is_dir():
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{src_dir}:{existing_pp}" if existing_pp else str(src_dir)

    cmd = list(layer.command)
    if cmd and cmd[0] in ("python", "python3"):
        cmd[0] = sys.executable

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=layer.timeout_seconds,
        )

        duration = time.perf_counter() - start_time
        output = (proc.stdout or "") + (proc.stderr or "")
        passed = proc.returncode == 0
        status = LayerExecutionStatus.PASSED if passed else LayerExecutionStatus.FAILED
        return LayerResult(
            name=layer.name,
            exit_code=proc.returncode,
            passed=passed,
            output=output,
            status=status,
            duration_seconds=duration,
            requirement=req,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - start_time
        output = f"Layer timed out after {layer.timeout_seconds}s: {exc}"
        return LayerResult(
            name=layer.name,
            exit_code=124,
            passed=False,
            output=output,
            status=LayerExecutionStatus.TIMED_OUT,
            duration_seconds=duration,
            requirement=req,
        )
    except OSError as exc:
        duration = time.perf_counter() - start_time
        output = f"Layer execution failed (OSError): {exc}"
        return LayerResult(
            name=layer.name,
            exit_code=127,
            passed=False,
            output=output,
            status=LayerExecutionStatus.UNAVAILABLE,
            duration_seconds=duration,
            requirement=req,
        )
    except Exception as exc:
        duration = time.perf_counter() - start_time
        output = f"Layer execution failed unexpectedly: {exc}"
        return LayerResult(
            name=layer.name,
            exit_code=1,
            passed=False,
            output=output,
            status=LayerExecutionStatus.ERROR,
            duration_seconds=duration,
            requirement=req,
        )


def run_gauntlet(
    layers: Sequence[LayerDefinition],
    cwd: str | Path | None = None,
) -> GauntletReport:
    """Execute verification layers in sequence, failing closed on first error."""
    if not layers:
        raise ValueError("Gauntlet requires at least one verification layer")

    overall_start = time.perf_counter()
    results: list[LayerResult] = []
    success = True

    for layer in layers:
        result = _execute_layer(layer, cwd=cwd)
        results.append(result)

        if not result.passed:
            if layer.requirement == LayerRequirement.REQUIRED and not layer.optional:
                success = False
                break

    total_duration = time.perf_counter() - overall_start
    return GauntletReport(
        success=success,
        layers=results,
        total_duration_seconds=total_duration,
    )
