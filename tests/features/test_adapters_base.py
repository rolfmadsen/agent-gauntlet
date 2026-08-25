"""Unit tests for the base adapter abstractions and models."""

import unittest

from agent_gauntlet.features.adapters import SUPPORTED_HARNESSES, get_adapter
from agent_gauntlet.features.adapters.models import (
    AdapterValidationResult,
    NormalizedToolCall,
    ToolActionType,
    ValidationIssue,
    ValidationSeverity,
)


class TestAdaptersBase(unittest.TestCase):
    """Test suite for adapter models and registry."""

    def test_tool_action_types_defined(self) -> None:
        """All fundamental tool action types are defined as expected strings."""
        self.assertEqual(ToolActionType.EXECUTE_COMMAND.value, "EXECUTE_COMMAND")
        self.assertEqual(ToolActionType.WRITE_FILE.value, "WRITE_FILE")
        self.assertEqual(ToolActionType.READ_FILE.value, "READ_FILE")
        self.assertEqual(ToolActionType.OTHER.value, "OTHER")

    def test_normalized_tool_call_creation(self) -> None:
        """NormalizedToolCall correctly stores normalized action details."""
        call = NormalizedToolCall(
            action_type=ToolActionType.EXECUTE_COMMAND,
            target_resource="pytest -v",
            raw_tool_name="run_command",
            payload={"CommandLine": "pytest -v"},
        )
        self.assertEqual(call.action_type, ToolActionType.EXECUTE_COMMAND)
        self.assertEqual(call.target_resource, "pytest -v")
        self.assertEqual(call.raw_tool_name, "run_command")
        self.assertEqual(call.payload, {"CommandLine": "pytest -v"})

    def test_adapter_validation_result(self) -> None:
        """AdapterValidationResult correctly tracks validity and issues."""
        ok_result = AdapterValidationResult(valid=True, issues=[])
        self.assertTrue(ok_result.valid)
        self.assertEqual(len(ok_result.issues), 0)

        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path="plugin.json",
            message="Missing required field 'version'",
        )
        failed_result = AdapterValidationResult(valid=False, issues=[issue])
        self.assertFalse(failed_result.valid)
        self.assertEqual(len(failed_result.issues), 1)
        self.assertEqual(failed_result.issues[0].message, "Missing required field 'version'")

    def test_get_adapter_antigravity(self) -> None:
        """get_adapter('antigravity') returns AntigravityAdapter instance."""
        adapter = get_adapter("antigravity")
        self.assertEqual(adapter.name, "antigravity")

    def test_get_adapter_unknown_raises_value_error(self) -> None:
        """get_adapter with unknown harness name raises ValueError."""
        with self.assertRaises(ValueError):
            get_adapter("nonexistent_harness")

    def test_supported_harnesses_list(self) -> None:
        """SUPPORTED_HARNESSES contains 'antigravity'."""
        self.assertIn("antigravity", SUPPORTED_HARNESSES)
