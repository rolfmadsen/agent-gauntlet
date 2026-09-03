#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/src/agent_gauntlet/features/supervisor/wasm"
PKG_OUTPUT_DIR="${REPO_ROOT}/packages/agent-gauntlet/src/agent_gauntlet/features/supervisor/wasm"

echo "==> Building gauntlet-policy-engine (native & wasm32)..."
cargo build --release --manifest-path "${SCRIPT_DIR}/Cargo.toml"
cargo build --target wasm32-unknown-unknown --release --manifest-path "${SCRIPT_DIR}/Cargo.toml"

echo "==> Copying artifacts to ${OUTPUT_DIR} and ${PKG_OUTPUT_DIR}..."
mkdir -p "${OUTPUT_DIR}" "${PKG_OUTPUT_DIR}"
cp "${SCRIPT_DIR}/target/release/libgauntlet_policy_engine.so" "${OUTPUT_DIR}/libpolicy_engine.so"
cp "${SCRIPT_DIR}/target/wasm32-unknown-unknown/release/gauntlet_policy_engine.wasm" "${OUTPUT_DIR}/policy_engine.wasm"
cp "${SCRIPT_DIR}/target/release/libgauntlet_policy_engine.so" "${PKG_OUTPUT_DIR}/libpolicy_engine.so"
cp "${SCRIPT_DIR}/target/wasm32-unknown-unknown/release/gauntlet_policy_engine.wasm" "${PKG_OUTPUT_DIR}/policy_engine.wasm"

echo "==> Artifact digests:"
sha256sum "${OUTPUT_DIR}/policy_engine.wasm"
sha256sum "${OUTPUT_DIR}/libpolicy_engine.so"
echo "==> Build complete."
