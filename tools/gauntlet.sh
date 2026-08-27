#!/bin/sh
# Gauntlet entry point for agent-gauntlet
# Runs all verification layers; fails fast on first broken layer.
set -e

cd "$(dirname "$0")/.."

PYTHON_BIN="$(which python3 || which python)"

if [ -d ".venv/.venv/lib/python3.14/site-packages" ]; then
    export PYTHONPATH="src:.venv/.venv/lib/python3.14/site-packages:$PYTHONPATH"
elif [ -d ".venv/lib/python3.12/site-packages" ]; then
    export PYTHONPATH="src:.venv/lib/python3.12/site-packages:$PYTHONPATH"
else
    export PYTHONPATH="src:$PYTHONPATH"
fi

echo "=== Layer 1: Code Formatting & Static Analysis (Ruff) ==="
$PYTHON_BIN -m ruff check .
$PYTHON_BIN -m ruff format --check .

echo "=== Layer 2: Strict Type Checking (Pyright) ==="
$PYTHON_BIN -m pyright src tests tools

echo "=== Layer 3: Unit & Acceptance Tests ==="
$PYTHON_BIN -m unittest discover tests

echo "=== Layer 4: Property & Invariant Tests ==="
$PYTHON_BIN -m unittest tests/features/test_gauntlet_properties.py

echo "=== Layer 5: Mutation Testing Negative Control ==="
$PYTHON_BIN tools/mutants.py --negative-control

echo "=== Layer 6: Mutation Testing Gauntlet ==="
$PYTHON_BIN tools/mutants.py

echo "=== Layer 7: Source State Tree Binding ==="
$PYTHON_BIN tools/source_state.py

echo ""
echo ">>> ALL GAUNTLET LAYERS PASSED <<<"
