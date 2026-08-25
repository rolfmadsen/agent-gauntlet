"""Unit and integration tests for gauntlet configuration loading and serialization."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_gauntlet.features.config.loader import (
    generate_default_config_toml,
    load_config,
)
from agent_gauntlet.features.config.schema import LayerConfig


class TestConfigSchemaAndLoader(unittest.TestCase):
    """Tests for configuration schema validation, TOML/JSON loading and fallback."""

    def test_layer_config_to_layer_definition(self) -> None:
        cfg = LayerConfig(name="test-layer", command=["pytest", "-v"], optional=True, timeout_seconds=45.0)
        defn = cfg.to_layer_definition()
        self.assertEqual(defn.name, "test-layer")
        self.assertEqual(list(defn.command), ["pytest", "-v"])
        self.assertTrue(defn.optional)
        self.assertEqual(defn.timeout_seconds, 45.0)

    def test_layer_config_command_as_string(self) -> None:
        cfg = LayerConfig(name="test-str", command="pytest -v")
        defn = cfg.to_layer_definition()
        self.assertEqual(list(defn.command), ["pytest", "-v"])

    def test_load_config_from_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_content = """
stack = "python"
save_evidence = true

[[layers]]
name = "unit"
command = ["pytest", "tests/"]
optional = false
timeout_seconds = 30.0

[[layers]]
name = "lint"
command = ["ruff", "check"]
optional = true
"""
            (Path(tmpdir) / "gauntlet.toml").write_text(toml_content)
            config = load_config(tmpdir)
            self.assertEqual(config.stack, "python")
            self.assertTrue(config.save_evidence)
            self.assertEqual(len(config.layers), 2)
            self.assertEqual(config.layers[0].name, "unit")
            self.assertFalse(config.layers[0].optional)
            self.assertEqual(config.layers[1].name, "lint")
            self.assertTrue(config.layers[1].optional)

    def test_load_config_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_content = {
                "stack": "typescript",
                "save_evidence": True,
                "layers": [
                    {
                        "name": "lint",
                        "command": ["npx", "eslint", "."],
                        "optional": True,
                    },
                    {
                        "name": "unit",
                        "command": ["npm", "test"],
                        "optional": False,
                    },
                ],
            }
            (Path(tmpdir) / "gauntlet.json").write_text(json.dumps(json_content))
            config = load_config(tmpdir)
            self.assertEqual(config.stack, "typescript")
            self.assertEqual(len(config.layers), 2)
            self.assertEqual(config.layers[0].name, "lint")

    def test_load_config_fallback_to_detected_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Cargo.toml").touch()
            config = load_config(tmpdir)
            self.assertEqual(config.stack, "rust")
            self.assertGreaterEqual(len(config.layers), 3)

    def test_generate_default_config_toml(self) -> None:
        toml_str = generate_default_config_toml("python")
        self.assertIn('stack = "python"', toml_str)
        self.assertIn("[[layers]]", toml_str)


if __name__ == "__main__":
    unittest.main()
