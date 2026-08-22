"""Manual mutation testing runner for agent-gauntlet.

Usage: python3 tools/mutants.py [test-target]
Exit code 0 iff every mutant is killed and negative control passes.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_RUNNER = ROOT / "src/agent_gauntlet/features/gauntlet/runner.py"
TARGET_AUTHORITY = ROOT / "src/agent_gauntlet/features/evidence/authority.py"
TARGET_GATEKEEPER = ROOT / "src/agent_gauntlet/features/hooks/gatekeeper.py"
TARGET_SCAFFOLDER = ROOT / "src/agent_gauntlet/features/scaffold/scaffolder.py"
TARGET_CLI = ROOT / "src/agent_gauntlet/cli.py"
def _clean_pycache() -> None:
    for p in ROOT.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)

MUTANT_ENV = {
    **os.environ,
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}:{os.environ.get('PYTHONPATH', '')}",
}

CORE_TESTS = [
    "tests.features.test_gauntlet",
    "tests.features.test_gauntlet_properties",
    "tests.features.test_evidence",
]

HOOK_TESTS = [
    "tests.features.test_hooks",
]

SCAFFOLD_TESTS = [
    "tests.features.test_scaffold",
]

CLI_TESTS = [
    "tests.test_cli.TestCliAcceptance.test_tree_hash_command",
    "tests.test_cli.TestCliAcceptance.test_check_evidence_valid",
    "tests.test_cli.TestCliAcceptance.test_check_evidence_tampered_fails",
    "tests.test_cli.TestCliAcceptance.test_check_evidence_drifted_fails",
]

MUTANTS = [
    # --- run_gauntlet mutants ---
    (
        TARGET_RUNNER,
        "M1 drop empty layers validation",
        "    if not layers:\n        raise ValueError(\"Gauntlet requires at least one verification layer\")\n",
        "",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M2 invert passed returncode comparison",
        "passed=proc.returncode == 0,",
        "passed=proc.returncode != 0,",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M3 invert failure detection check",
        "        if not result.passed:",
        "        if result.passed:",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M4 ignore optional flag on failure (abort on optional)",
        "            if not layer.optional:\n                success = False\n                break",
        "            if True:\n                success = False\n                break",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M5 ignore mandatory failures (never set success to False)",
        "            if not layer.optional:\n                success = False\n                break",
        "            if not layer.optional:\n                pass",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M6 fail-open: failing layer sets success to True",
        "                success = False",
        "                success = True",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M7 fail-open: do not halt on broken mandatory layer (drop break)",
        "                success = False\n                break",
        "                success = False",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M8 mask timeout exit_code as 0 and passed=True",
        "            exit_code=124,\n            passed=False,",
        "            exit_code=0,\n            passed=True,",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M9 mask OSError exit_code as 0 and passed=True",
        "            exit_code=127,\n            passed=False,",
        "            exit_code=0,\n            passed=True,",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M10 drop recording of layer results",
        "        results.append(result)",
        "        pass",
        CORE_TESTS,
    ),
    # --- evidence_authority mutants ---
    (
        TARGET_AUTHORITY,
        "EA-M1 fail-open on missing signature",
        "        if not record.signature or not isinstance(record.signature, str):\n            return False",
        "        if not record.signature or not isinstance(record.signature, str):\n            return True",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "EA-M2 always accept signature (bypass verify)",
        "        return hmac.compare_digest(record.signature, expected_signature)",
        "        return True",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "EA-M3 always reject signature",
        "        return hmac.compare_digest(record.signature, expected_signature)",
        "        return False",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "EA-M4 bypass record verification in tree match check",
        "        if not self.verify_record(record):\n            return False",
        "        pass",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "EA-M5 bypass tree hash comparison in tree match check",
        "        return hmac.compare_digest(record.source_tree_hash, str(current_tree_hash))",
        "        return True",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "EA-M6 drop signature generation",
        "        signature = hmac.new(self._key, payload, hashlib.sha256).hexdigest()",
        "        signature = \"\"",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "EA-M7 drop criteria from canonical payload",
        '            "acceptance_criteria": sorted(list(record.acceptance_criteria)),',
        '            "acceptance_criteria": [],',
        CORE_TESTS,
    ),
    # --- gatekeeper mutants ---
    (
        TARGET_GATEKEEPER,
        "GK-M1 gatekeeper bypass active task check",
        "            if not has_active_task(workspace):",
        "            if False:",
        HOOK_TESTS,
    ),
    (
        TARGET_GATEKEEPER,
        "GK-M2 gatekeeper allow forbidden remote commands",
        "            if re.search(pattern, command_line, re.IGNORECASE):",
        "            if False:",
        HOOK_TESTS,
    ),
    # --- scaffold mutants ---
    (
        TARGET_SCAFFOLDER,
        "SCF-M1 always overwrite without force check",
        "            if force:",
        "            if True:",
        SCAFFOLD_TESTS,
    ),
    (
        TARGET_SCAFFOLDER,
        "SCF-M2 drop file creation in safe write",
        '        target_path.parent.mkdir(parents=True, exist_ok=True)\n        target_path.write_text(content, encoding="utf-8")',
        "        target_path.parent.mkdir(parents=True, exist_ok=True)",
        SCAFFOLD_TESTS,
    ),
    # --- cli mutants ---
    (
        TARGET_CLI,
        "CLI-M1 check-evidence fail-open on invalid signature",
        "        if not authority.verify_record(record):",
        "        if False:",
        CLI_TESTS,
    ),
    (
        TARGET_CLI,
        "CLI-M2 check-evidence fail-open on drifted tree hash",
        "        if not authority.verify_source_state_match(record, current_tree):",
        "        if False:",
        CLI_TESTS,
    ),
]

CONTROL = [
    (
        TARGET_RUNNER,
        "C1 killer (control)",
        "passed=proc.returncode == 0,",
        "passed=True,",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "C2 equivalent (control)",
        'output = (proc.stdout or "") + (proc.stderr or "")',
        'output = ("" if proc.stdout is None else proc.stdout) + ("" if proc.stderr is None else proc.stderr)',
        CORE_TESTS,
    ),
]


def run_mutant(
    target_file: Path,
    original: str,
    old: str,
    new: str,
    tests: list[str],
    pin_mtime: float = 0.0,
) -> int:
    """Apply one mutant and run specified test suite."""
    target_file.write_text(original.replace(old, new, 1))
    if pin_mtime:
        os.utime(target_file, (pin_mtime, pin_mtime))
    _clean_pycache()

    cmd = [sys.executable, "-m", "unittest", *tests]

    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=MUTANT_ENV,
    )
    return result.returncode


def negative_control() -> int:
    """Prove the harness can tell a killer from an equivalent mutant."""
    original = TARGET_RUNNER.read_text()
    try:
        pinned = 1_600_000_000.0
        codes = [
            run_mutant(target_file, original, old, new, tests, pin_mtime=pinned)
            for target_file, _, old, new, tests in CONTROL
        ]
    finally:
        TARGET_RUNNER.write_text(original)
        _clean_pycache()

    if TARGET_RUNNER.read_text() != original:
        raise RuntimeError("negative control did not restore original source")

    ok = codes == [1, 0]
    for (_, name, _, _, _), code in zip(CONTROL, codes, strict=True):
        verdict = {1: "KILLED", 0: "SURVIVED"}.get(code, f"ERROR (exit {code})")
        print(f"  {name}: {verdict}")
    print("  negative control: " + ("ok" if ok else "FAILED — harness misreports"))
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--negative-control":
        return negative_control()

    killed = 0
    errors = 0

    originals: dict[Path, str] = {
        TARGET_RUNNER: TARGET_RUNNER.read_text(),
        TARGET_AUTHORITY: TARGET_AUTHORITY.read_text(),
        TARGET_GATEKEEPER: TARGET_GATEKEEPER.read_text(),
        TARGET_SCAFFOLDER: TARGET_SCAFFOLDER.read_text(),
        TARGET_CLI: TARGET_CLI.read_text(),
    }

    try:
        for target_file, name, old, new, tests in MUTANTS:
            original = originals[target_file]
            assert (
                original.count(old) == 1
            ), f"{name}: pattern '{old}' not unique (count={original.count(old)}) in {target_file.name}"
            returncode = run_mutant(target_file, original, old, new, tests)
            target_file.write_text(original)

            if returncode == 1:
                status = "KILLED"
                killed += 1
            elif returncode == 0:
                status = "SURVIVED"
            else:
                status = f"ERROR (exit {returncode})"
                errors += 1
            print(f"{name}: {status}")
    finally:
        for target_file, original in originals.items():
            target_file.write_text(original)
        _clean_pycache()

    summary = f"\n{killed}/{len(MUTANTS)} mutants killed"
    if errors:
        summary += f", {errors} ERROR — run is invalid"
    print(summary)
    return 0 if killed == len(MUTANTS) and errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
