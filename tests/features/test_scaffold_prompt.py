"""Unit and integration tests for interactive stack selection on scaffold/init."""

import io
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_gauntlet.features.scaffold.prompt import prompt_for_stack, resolve_scaffold_stack


class TestScaffoldPrompt(unittest.TestCase):
    """Tests for interactive stack prompting and resolution."""

    def test_prompt_for_stack_number_selection(self) -> None:
        """User typing '1', '2', or '3' selects python, typescript, or rust."""
        stream_in = io.StringIO("1\n")
        stream_out = io.StringIO()
        self.assertEqual(prompt_for_stack(stdin=stream_in, stdout=stream_out), "python")

        stream_in = io.StringIO("2\n")
        self.assertEqual(prompt_for_stack(stdin=stream_in, stdout=stream_out), "typescript")

        stream_in = io.StringIO("3\n")
        self.assertEqual(prompt_for_stack(stdin=stream_in, stdout=stream_out), "rust")

    def test_prompt_for_stack_name_and_alias_selection(self) -> None:
        """User typing name or alias selects the stack case-insensitively."""
        stream_out = io.StringIO()

        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("typescript\n"), stdout=stream_out), "typescript"
        )
        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("TypeScript\n"), stdout=stream_out), "typescript"
        )
        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("ts\n"), stdout=stream_out), "typescript"
        )

        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("python\n"), stdout=stream_out), "python"
        )
        self.assertEqual(prompt_for_stack(stdin=io.StringIO("py\n"), stdout=stream_out), "python")

        self.assertEqual(prompt_for_stack(stdin=io.StringIO("rust\n"), stdout=stream_out), "rust")
        self.assertEqual(prompt_for_stack(stdin=io.StringIO("rs\n"), stdout=stream_out), "rust")

    def test_prompt_for_stack_comma_separated_polyglot_selection(self) -> None:
        """User typing '1, 2' or 'typescript, rust' selects multiple stacks for polyglot workspace."""
        stream_out = io.StringIO()
        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("1, 2\n"), stdout=stream_out), "python, typescript"
        )
        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("typescript, rust\n"), stdout=stream_out),
            "typescript, rust",
        )
        self.assertEqual(
            prompt_for_stack(stdin=io.StringIO("ts, py, rust\n"), stdout=stream_out),
            "typescript, python, rust",
        )

    def test_prompt_for_stack_empty_input_defaults_to_python(self) -> None:
        """Pressing enter with no input defaults to python."""
        stream_in = io.StringIO("\n")
        stream_out = io.StringIO()
        self.assertEqual(prompt_for_stack(stdin=stream_in, stdout=stream_out), "python")

    def test_prompt_for_stack_invalid_input_reprompts(self) -> None:
        """Invalid input prints error message and reprompts until valid input is given."""
        stream_in = io.StringIO("invalid\n4\n2\n")
        stream_out = io.StringIO()
        choice = prompt_for_stack(stdin=stream_in, stdout=stream_out)
        self.assertEqual(choice, "typescript")
        output = stream_out.getvalue()
        self.assertIn("Ugyldigt valg", output)

    def test_prompt_for_stack_eof_handled_gracefully(self) -> None:
        """EOF on input stream raises InterruptedError cleanly."""
        stream_in = io.StringIO("")  # Immediate EOF
        stream_out = io.StringIO()
        with self.assertRaises(InterruptedError):
            prompt_for_stack(stdin=stream_in, stdout=stream_out)

    def test_resolve_scaffold_stack_explicit_stack_skips_prompt(self) -> None:
        """When explicit stack is provided, no prompt is executed."""
        stream_in = io.StringIO("2\n")
        stream_out = io.StringIO()
        stacks = resolve_scaffold_stack(
            explicit_stack="rust",
            workspace=Path("/dummy"),
            interactive=True,
            stdin=stream_in,
            stdout=stream_out,
        )
        self.assertEqual(stacks, ["rust"])
        self.assertEqual(stream_out.getvalue(), "")

    def test_resolve_scaffold_stack_detected_stack_skips_prompt(self) -> None:
        """When workspace has detected stacks, no prompt is executed."""
        stream_in = io.StringIO("2\n")
        stream_out = io.StringIO()
        with patch(
            "agent_gauntlet.features.scaffold.prompt.detect_stacks", return_value=["typescript"]
        ):
            stacks = resolve_scaffold_stack(
                explicit_stack=None,
                workspace=Path("/dummy"),
                interactive=True,
                stdin=stream_in,
                stdout=stream_out,
            )
        self.assertEqual(stacks, ["typescript"])
        self.assertEqual(stream_out.getvalue(), "")

    def test_resolve_scaffold_stack_non_interactive_defaults_to_python(self) -> None:
        """When workspace is empty and interactive is False, defaults to python with advisory."""
        stream_in = io.StringIO("2\n")
        stream_out = io.StringIO()
        stream_err = io.StringIO()
        with patch("agent_gauntlet.features.scaffold.prompt.detect_stacks", return_value=[]):
            stacks = resolve_scaffold_stack(
                explicit_stack=None,
                workspace=Path("/dummy"),
                interactive=False,
                stdin=stream_in,
                stdout=stream_out,
                stderr=stream_err,
            )
        self.assertEqual(stacks, ["python"])
        self.assertIn("python", stream_err.getvalue())

    def test_resolve_scaffold_stack_interactive_prompts_user(self) -> None:
        """When workspace is empty and interactive is True, prompts user and returns selection."""
        stream_in = io.StringIO("2\n")
        stream_out = io.StringIO()
        with patch("agent_gauntlet.features.scaffold.prompt.detect_stacks", return_value=[]):
            stacks = resolve_scaffold_stack(
                explicit_stack=None,
                workspace=Path("/dummy"),
                interactive=True,
                stdin=stream_in,
                stdout=stream_out,
            )
        self.assertEqual(stacks, ["typescript"])
        self.assertIn("Hvilken primær stack bygger du på?", stream_out.getvalue())
