#!/bin/sh
# Gauntlet entry point for agent-gauntlet
# Runs all verification layers; fails fast on first broken layer.
set -e

cd "$(dirname "$0")/.."

echo "=== Layer 1: Unit & Acceptance Tests ==="
PYTHONPATH=src python3 -m unittest discover tests

echo "=== Layer 2: Property & Invariant Tests ==="
PYTHONPATH=src python3 -m unittest tests/features/test_gauntlet_properties.py

echo "=== Layer 3: Mutation Testing Negative Control ==="
python3 tools/mutants.py --negative-control

echo "=== Layer 4: Mutation Testing Gauntlet ==="
python3 tools/mutants.py

echo "=== Layer 5: Source State Tree Binding ==="
python3 tools/source_state.py

echo ""
echo ">>> ALL GAUNTLET LAYERS PASSED <<<"
