"""Multi-layer verification runner for agent-gauntlet."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Sequence

from agent_gauntlet.features.gauntlet.models import (
    GauntletReport,
    LayerDefinition,
    LayerResult,
)


def _execute_layer(
    layer: LayerDefinition,
    cwd: str | Path | None = None,
) -> LayerResult:
    """Execute a single layer command and capture output, exit code and duration."""
    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            list(layer.command),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=layer.timeout_seconds,
        )
        duration = time.perf_counter() - start_time
        output = (proc.stdout or "") + (proc.stderr or "")
        return LayerResult(
            name=layer.name,
            exit_code=proc.returncode,
            passed=proc.returncode == 0,
            output=output,
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - start_time
        output = f"Layer timed out after {layer.timeout_seconds}s: {exc}"
        return LayerResult(
            name=layer.name,
            exit_code=124,
            passed=False,
            output=output,
            duration_seconds=duration,
        )
    except OSError as exc:
        duration = time.perf_counter() - start_time
        output = f"Layer execution failed (OSError): {exc}"
        return LayerResult(
            name=layer.name,
            exit_code=127,
            passed=False,
            output=output,
            duration_seconds=duration,
        )
    except Exception as exc:
        duration = time.perf_counter() - start_time
        output = f"Layer execution failed unexpectedly: {exc}"
        return LayerResult(
            name=layer.name,
            exit_code=1,
            passed=False,
            output=output,
            duration_seconds=duration,
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
            if not layer.optional:
                success = False
                break

    total_duration = time.perf_counter() - overall_start
    return GauntletReport(
        success=success,
        layers=results,
        total_duration_seconds=total_duration,
    )
