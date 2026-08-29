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
TARGET_AUTHORITY = ROOT / "src/agent_gauntlet/features/evidence/report.py"
TARGET_MANIFEST = ROOT / "src/agent_gauntlet/features/evidence/source_state.py"
TARGET_TRUST = ROOT / "src/agent_gauntlet/features/evidence/trust_policy.py"
TARGET_ATTESTATION = ROOT / "src/agent_gauntlet/features/evidence/attestation.py"
TARGET_GATEKEEPER = ROOT / "src/agent_gauntlet/features/hooks/gatekeeper.py"
TARGET_SCAFFOLDER = ROOT / "src/agent_gauntlet/features/scaffold/scaffolder.py"
TARGET_ADAPTER = ROOT / "src/agent_gauntlet/features/adapters/antigravity/adapter.py"
TARGET_VALIDATOR = ROOT / "src/agent_gauntlet/features/adapters/antigravity/validator.py"
TARGET_CURSOR_ADAPTER = ROOT / "src/agent_gauntlet/features/adapters/cursor/adapter.py"
TARGET_CURSOR_VALIDATOR = ROOT / "src/agent_gauntlet/features/adapters/cursor/validator.py"
TARGET_OKF_VALIDATOR = ROOT / "src/agent_gauntlet/features/okf/validator.py"
TARGET_OKF_STAMPER = ROOT / "src/agent_gauntlet/features/okf/stamper.py"
TARGET_CLI = ROOT / "src/agent_gauntlet/cli.py"
TARGET_VERIFIER = ROOT / "src/agent_gauntlet/features/evidence/verifier.py"
TARGET_NPX_WRAPPER = ROOT / "packages/agent-gauntlet/bin/agent-gauntlet.js"


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
    "tests.features.test_manifest",
    "tests.features.test_attestation",
]

HOOK_TESTS = [
    "tests.features.test_hooks",
]

ADAPTER_TESTS = [
    "tests.features.test_adapter_antigravity",
    "tests.features.test_adapter_cursor",
    "tests.features.test_adapters_base",
]

OKF_TESTS = [
    "tests.features.test_okf",
]

SCAFFOLD_TESTS = [
    "tests.features.test_scaffold",
]

CLI_TESTS = [
    "tests.test_cli",
]

NPX_TESTS = [
    "tests.features.test_npx_wrapper",
]


MUTANTS = [
    # --- run_gauntlet mutants ---
    (
        TARGET_RUNNER,
        "M1 drop empty layers validation",
        '    if not layers:\n        raise ValueError("Gauntlet requires at least one verification layer")\n',
        "",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M2 invert passed returncode comparison",
        "passed = proc.returncode == 0",
        "passed = proc.returncode != 0",
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
        "            if layer.requirement == LayerRequirement.REQUIRED and not layer.optional:\n                success = False\n                break",
        "            if True:\n                success = False\n                break",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "M5 ignore mandatory failures (never set success to False)",
        "            if layer.requirement == LayerRequirement.REQUIRED and not layer.optional:\n                success = False\n                break",
        "            if layer.requirement == LayerRequirement.REQUIRED and not layer.optional:\n                pass",
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
    # --- verification_report mutants ---
    (
        TARGET_AUTHORITY,
        "VR-M1 fail-open on drifted manifest match",
        "        if not hmac.compare_digest(report_digest, cur_digest):",
        "        if False and not hmac.compare_digest(report_digest, cur_digest):",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "VR-M2 always reject manifest match",
        "        return True",
        "        return False",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "VR-M3 fail-open on empty report digest",
        "        if not report_digest or not cur_digest:\n            return False",
        "        if not report_digest or not cur_digest:\n            return True",
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "VR-M4 classify_evidence_payload invert legacy check",
        '        if "signature" in data or "source_tree_hash" in data:\n            return "LEGACY_UNATTESTED"',
        '        if "signature" in data or "source_tree_hash" in data:\n            return "LOCAL_UNATTESTED"',
        CORE_TESTS,
    ),
    (
        TARGET_AUTHORITY,
        "VR-M5 load_report_json drop verdict parsing",
        '                verdict=str(data.get("verdict", "PASSED")),',
        '                verdict="PASSED",',
        CORE_TESTS,
    ),
    # --- workspace_manifest mutants ---
    (
        TARGET_MANIFEST,
        "MNF-M1 symlink escape check bypass",
        "                try:\n                    # Check workspace escape: resolved target must be within target_root\n                    resolved.relative_to(target_root)\n                except ValueError as err:\n                    raise WorkspaceEscapeError(",
        "                try:\n                    pass\n                except ValueError as err:\n                    raise WorkspaceEscapeError(",
        CORE_TESTS,
    ),
    (
        TARGET_MANIFEST,
        "MNF-M2 ignore file mode bit in manifest lines",
        '        manifest_hasher.update(m.encode("ascii"))',
        '        manifest_hasher.update(b"0")',
        CORE_TESTS,
    ),
    (
        TARGET_MANIFEST,
        "MNF-M3 ignore excluded files in manifest",
        "            if _is_excluded(rel_path):\n                continue",
        "            if False:\n                continue",
        CORE_TESTS,
    ),
    # --- trust_policy mutants ---
    (
        TARGET_TRUST,
        "TRP-M1 fail-open on unauthorized issuer",
        "            if identity.issuer not in policy.allowed_oidc_issuers:",
        "            if False:",
        CORE_TESTS,
    ),
    (
        TARGET_TRUST,
        "TRP-M2 fail-open on failed verdict in release_eligible",
        '            and report.verdict == "PASSED"',
        "            and True",
        CORE_TESTS,
    ),
    (
        TARGET_TRUST,
        "TRP-M3 fail-open on invalid attestation status",
        "            elif attestation.status != AttestationStatus.VALID:",
        "            elif False:",
        CORE_TESTS,
    ),
    # --- attestation mutants ---
    (
        TARGET_ATTESTATION,
        "ATT-M1 bypass subject digest comparison",
        "        if not bundle.subject_digest or not hmac.compare_digest(\n            bundle.subject_digest, expected_subject_digest\n        ):",
        "        if False:",
        CORE_TESTS,
    ),
    # --- gatekeeper mutants ---
    (
        TARGET_GATEKEEPER,
        "GK-M1 gatekeeper bypass active task check",
        "            if is_protected and not context.has_active_task:",
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
    # --- adapter mutants ---
    (
        TARGET_ADAPTER,
        "AD-M1 normalize_tool_call invert command check",
        '        if tool_name == "run_command":',
        '        if tool_name != "run_command":',
        ADAPTER_TESTS,
    ),
    (
        TARGET_ADAPTER,
        "AD-M2 evaluate_invocation fail-open decision",
        "            decision=decision.decision,",
        '            decision="allow",',
        ADAPTER_TESTS,
    ),
    (
        TARGET_ADAPTER,
        "AD-M3 evaluate_invocation fail-open allowed flag",
        "            allowed=decision.allowed,",
        "            allowed=True,",
        ADAPTER_TESTS,
    ),
    (
        TARGET_VALIDATOR,
        "VAL-M1 validator ignore missing manifest",
        "        if not manifest_file.is_file():",
        "        if False:",
        ADAPTER_TESTS,
    ),
    (
        TARGET_VALIDATOR,
        "VAL-M2 validator ignore missing skill",
        "                    if not skill_file.is_file():",
        "                    if False:",
        ADAPTER_TESTS,
    ),
    # --- cursor adapter mutants ---
    (
        TARGET_CURSOR_ADAPTER,
        "CUR-AD-M1 normalize_tool_call invert command check",
        '        if tool_name in (\n            "run_terminal_command",\n            "run_command",\n            "terminal",\n            "bash",\n            "execute_command",\n            "command",\n        ):',
        "        if False:",
        ADAPTER_TESTS,
    ),
    (
        TARGET_CURSOR_ADAPTER,
        "CUR-AD-M2 evaluate_invocation fail-open decision",
        "            decision=decision.decision,",
        '            decision="allow",',
        ADAPTER_TESTS,
    ),
    (
        TARGET_CURSOR_ADAPTER,
        "CUR-AD-M3 evaluate_invocation fail-open allowed flag",
        "            allowed=decision.allowed,",
        "            allowed=True,",
        ADAPTER_TESTS,
    ),
    (
        TARGET_CURSOR_VALIDATOR,
        "CUR-VAL-M1 validator ignore missing rule files",
        "        if not rule_files:",
        "        if False:",
        ADAPTER_TESTS,
    ),
    (
        TARGET_CURSOR_VALIDATOR,
        "CUR-VAL-M2 validator ignore missing alwaysApply",
        "        if always_apply is None:",
        "        if False:",
        ADAPTER_TESTS,
    ),
    (
        TARGET_SCAFFOLDER,
        "CUR-SCF-M1 ignore cursor harness scaffolding",
        '        if harness == "cursor":',
        "        if False:",
        ADAPTER_TESTS,
    ),
    # --- cli & verifier mutants ---
    (
        TARGET_VERIFIER,
        "CLI-M1 check-evidence fail-open on legacy evidence",
        '    if classification == "LEGACY_UNATTESTED":',
        "    if False:",
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M2 check-evidence fail-open on drifted manifest match",
        "    if not engine.verify_workspace_state_match(\n        report_obj,\n        current_manifest.source_manifest_digest,\n        current_manifest.policy_digest,\n        current_manifest.config_digest,\n        current_manifest.task_digest,\n    ):",
        "    if False:",
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M3 check-attestation ignore drift error",
        "    if not report_engine.verify_workspace_state_match(\n        report_obj,\n        current_manifest.source_manifest_digest,\n        current_manifest.policy_digest,\n        current_manifest.config_digest,\n        current_manifest.task_digest,\n    ):",
        "    if False:",
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M4 check-attestation fail-open on failed verdict",
        "    if allow_unattested and attestation_status_val == AttestationStatus.ABSENT.value:",
        "    if True:",
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M5 verify ignore unresolved criteria",
        '    elif unresolved:\n        verdict = "INCOMPLETE"',
        '    elif False:\n        verdict = "INCOMPLETE"',
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M6 verify targeted test fail-open to PASSED",
        '    elif test_target:\n        verdict = "PARTIAL"',
        '    elif False:\n        verdict = "PARTIAL"',
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M7 check-evidence fail-open on unresolved criteria",
        "    if report_obj.task_contract.unresolved_criteria:",
        "    if False:",
        CLI_TESTS,
    ),
    (
        TARGET_VERIFIER,
        "CLI-M8 check-evidence fail-open on failed checks",
        "    if failed_checks:",
        "    if False:",
        CLI_TESTS,
    ),
    (
        TARGET_RUNNER,
        "INV-M1 mask OSError as PASSED status",
        "            status=LayerExecutionStatus.UNAVAILABLE,",
        "            status=LayerExecutionStatus.PASSED,",
        CORE_TESTS,
    ),
    (
        TARGET_RUNNER,
        "INV-M2 mask Timeout as PASSED status",
        "            status=LayerExecutionStatus.TIMED_OUT,",
        "            status=LayerExecutionStatus.PASSED,",
        CORE_TESTS,
    ),
    # --- OKF validator & stamper mutants ---
    (
        TARGET_OKF_VALIDATOR,
        "M_OKF1 ignore required type check",
        "    if not doc_type or not str(doc_type).strip():",
        "    if False:",
        OKF_TESTS,
    ),
    (
        TARGET_OKF_VALIDATOR,
        "M_OKF2 ignore future timestamp check in generated",
        "                    generated_dt = dt\n                    if dt is not None and dt > future_tolerance:",
        "                    generated_dt = dt\n                    if False:",
        OKF_TESTS,
    ),
    (
        TARGET_OKF_VALIDATOR,
        "M_OKF3 ignore chronological inversion check",
        "                    if generated_dt is not None and dt is not None and dt < generated_dt:",
        "                    if False:",
        OKF_TESTS,
    ),
    (
        TARGET_OKF_VALIDATOR,
        "M_OKF4 ignore missing source resource check",
        '                elif not src.get("resource") or not str(src.get("resource")).strip():',
        "                elif False:",
        OKF_TESTS,
    ),
    (
        TARGET_OKF_STAMPER,
        "M_OKF5 ignore status update in stamper",
        '    if status:\n        meta["status"] = status',
        '    if False:\n        meta["status"] = status',
        OKF_TESTS,
    ),
    # --- NPX wrapper mutants ---
    (
        TARGET_NPX_WRAPPER,
        "NPX-M1 fail-open on missing python binary",
        "  if (!pythonBin) {",
        "  if (false) {",
        NPX_TESTS,
    ),
    (
        TARGET_NPX_WRAPPER,
        "NPX-M2 drop CLI arguments forwarding",
        "  const args = process.argv.slice(2);",
        "  const args = [];",
        NPX_TESTS,
    ),
]


CONTROL = [
    (
        TARGET_RUNNER,
        "C1 killer (control)",
        "passed = proc.returncode == 0",
        "passed = True",
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
        TARGET_MANIFEST: TARGET_MANIFEST.read_text(),
        TARGET_TRUST: TARGET_TRUST.read_text(),
        TARGET_ATTESTATION: TARGET_ATTESTATION.read_text(),
        TARGET_GATEKEEPER: TARGET_GATEKEEPER.read_text(),
        TARGET_SCAFFOLDER: TARGET_SCAFFOLDER.read_text(),
        TARGET_ADAPTER: TARGET_ADAPTER.read_text(),
        TARGET_VALIDATOR: TARGET_VALIDATOR.read_text(),
        TARGET_CURSOR_ADAPTER: TARGET_CURSOR_ADAPTER.read_text(),
        TARGET_CURSOR_VALIDATOR: TARGET_CURSOR_VALIDATOR.read_text(),
        TARGET_OKF_VALIDATOR: TARGET_OKF_VALIDATOR.read_text(),
        TARGET_OKF_STAMPER: TARGET_OKF_STAMPER.read_text(),
        TARGET_CLI: TARGET_CLI.read_text(),
        TARGET_VERIFIER: TARGET_VERIFIER.read_text(),
        TARGET_NPX_WRAPPER: TARGET_NPX_WRAPPER.read_text(),
    }

    try:
        for target_file, name, old, new, tests in MUTANTS:
            original = originals[target_file]
            assert original.count(old) == 1, (
                f"{name}: pattern '{old}' not unique (count={original.count(old)}) in {target_file.name}"
            )
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
