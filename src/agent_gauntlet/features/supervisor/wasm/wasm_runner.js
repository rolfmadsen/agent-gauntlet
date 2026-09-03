#!/usr/bin/env node
const fs = require('fs');

async function main() {
  const wasmPath = process.argv[2];
  let reqJson = process.argv[3];
  let ctxJson = process.argv[4];

  if (!reqJson || !ctxJson) {
    try {
      const inputStr = fs.readFileSync(0, 'utf-8');
      if (inputStr.trim()) {
        const parsed = JSON.parse(inputStr);
        reqJson = typeof parsed.request === 'string' ? parsed.request : JSON.stringify(parsed.request);
        ctxJson = typeof parsed.context === 'string' ? parsed.context : JSON.stringify(parsed.context);
      }
    } catch (e) {
      // Handled by validation check below
    }
  }

  if (!wasmPath || !reqJson || !ctxJson) {
    process.stderr.write("Usage: wasm_runner.js <wasm_path> [<req_json> <ctx_json>] (or JSON envelope on stdin)\n");
    process.exit(1);
  }

  const wasmBuffer = fs.readFileSync(wasmPath);
  const wasmModule = await WebAssembly.instantiate(wasmBuffer);
  const exports = wasmModule.instance.exports;

  const encoder = new TextEncoder();
  const reqBytes = encoder.encode(reqJson);
  const ctxBytes = encoder.encode(ctxJson);

  const reqPtr = exports.alloc(reqBytes.length);
  const ctxPtr = exports.alloc(ctxBytes.length);

  new Uint8Array(exports.memory.buffer, reqPtr, reqBytes.length).set(reqBytes);
  new Uint8Array(exports.memory.buffer, ctxPtr, ctxBytes.length).set(ctxBytes);

  const res64 = exports.evaluate_json_wasm(reqPtr, reqBytes.length, ctxPtr, ctxBytes.length);
  const outLen = Number(res64 >> 32n);
  const outPtr = Number(res64 & 0xFFFFFFFFn);

  const outBytes = new Uint8Array(exports.memory.buffer, outPtr, outLen);
  const decoder = new TextDecoder();
  process.stdout.write(decoder.decode(outBytes));

  exports.dealloc(reqPtr, reqBytes.length);
  exports.dealloc(ctxPtr, ctxBytes.length);
  exports.dealloc(outPtr, outLen);
}

main().catch(err => {
  process.stderr.write(`WASM execution error: ${err.message}\n`);
  process.exit(1);
});
