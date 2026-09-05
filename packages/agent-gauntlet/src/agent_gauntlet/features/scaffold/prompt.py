"""Interactive stack selection prompt for project initialization in empty workspaces."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from agent_gauntlet.features.stacks.detector import detect_stacks

STACK_CHOICE_MAP: dict[str, str] = {
    "1": "python",
    "python": "python",
    "py": "python",
    "2": "typescript",
    "typescript": "typescript",
    "ts": "typescript",
    "3": "rust",
    "rust": "rust",
    "rs": "rust",
}

DEFAULT_STACK = "python"


def prompt_for_stack(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> str:
    """Prompts the user interactively to select a primary programming stack.

    Args:
        stdin: Input stream to read from (defaults to sys.stdin).
        stdout: Output stream to write to (defaults to sys.stdout).

    Returns:
        The selected stack name ('python', 'typescript', or 'rust').

    Raises:
        InterruptedError: If stdin is closed, EOF reached, or KeyboardInterrupt occurs.
    """
    stream_in = stdin if stdin is not None else sys.stdin
    stream_out = stdout if stdout is not None else sys.stdout

    options_text = (
        "\nHvilken primær stack bygger du på?\n"
        "  [1] Python (standard / default)\n"
        "  [2] TypeScript\n"
        "  [3] Rust\n"
    )
    stream_out.write(options_text)
    stream_out.flush()

    while True:
        stream_out.write("Vælg stack [1-3, standard: 1]: ")
        stream_out.flush()
        try:
            line = stream_in.readline()
            if not line:
                raise InterruptedError("Interactive prompt aborted: EOF reached on input stream.")
        except KeyboardInterrupt as exc:
            raise InterruptedError("Interactive prompt aborted by user (Ctrl+C).") from exc

        choice = line.strip().lower()
        if not choice:
            return DEFAULT_STACK

        parts = [p.strip() for p in choice.split(",") if p.strip()]
        normalized_parts = [STACK_CHOICE_MAP.get(p) for p in parts]
        if all(normalized_parts):
            seen: set[str] = set()
            unique = [p for p in normalized_parts if p and not (p in seen or seen.add(p))]
            return ", ".join(unique)

        stream_out.write(
            f"[!] Ugyldigt valg '{choice}'. Vælg venligst mellem 1 (python), 2 (typescript) eller 3 (rust) (eller f.eks. '1, 2' for polyglot).\n"
        )
        stream_out.flush()


def resolve_scaffold_stack(
    explicit_stack: str | None,
    workspace: Path | str,
    interactive: bool = True,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> list[str]:
    """Resolves target stack(s) for scaffolding, prompting if unidentifiable and interactive.

    Args:
        explicit_stack: Explicitly specified stack name(s) or None.
        workspace: Root path of the workspace.
        interactive: Whether interactive TTY prompting is allowed.
        stdin: Optional input stream for prompting.
        stdout: Optional output stream for prompting.
        stderr: Optional output stream for notices (defaults to sys.stderr).

    Returns:
        List of resolved stack names (e.g. ['python'] or ['typescript', 'python']).
    """
    if explicit_stack:
        return [s.strip() for s in explicit_stack.split(",") if s.strip()]

    ws_path = Path(workspace).resolve()
    detected = detect_stacks(ws_path)
    if detected:
        return detected

    # Workspace is empty or has no identifiable markers
    if not interactive:
        stream_err = stderr if stderr is not None else sys.stderr
        stream_err.write(
            f"[*] Ingen projektstak detekteret; anvender standardstak '{DEFAULT_STACK}'.\n"
        )
        stream_err.flush()
        return [DEFAULT_STACK]

    selected = prompt_for_stack(stdin=stdin, stdout=stdout)
    return [s.strip() for s in selected.split(",") if s.strip()]
