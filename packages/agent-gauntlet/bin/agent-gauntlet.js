#!/usr/bin/env node
/**
 * agent-gauntlet CLI wrapper for npm / npx.
 * Dispatches commands directly to agent_gauntlet Python core engine.
 */

const { spawnSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function findPythonBinary() {
  if (process.env.PYTHON_BIN) {
    return process.env.PYTHON_BIN;
  }
  const candidates = ['python3', 'python'];
  for (const bin of candidates) {
    try {
      const check = spawnSync(bin, ['--version'], { stdio: 'ignore' });
      if (check.status === 0) {
        return bin;
      }
    } catch (_) {
      // ignore and try next
    }
  }
  return null;
}

function resolvePythonPath() {
  const candidates = [
    path.resolve(__dirname, '..', 'src'),
    path.resolve(__dirname, '..', '..', '..', 'src'),
    path.resolve(__dirname, '..', '..', 'src'),
  ];
  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, 'agent_gauntlet', 'cli.py'))) {
      return dir;
    }
  }
  return null;
}

function main() {
  const pythonBin = findPythonBinary();
  if (!pythonBin) {
    console.error('[agent-gauntlet] Error: Python 3.10+ was not found on your system PATH.');
    console.error('[agent-gauntlet] Please install Python 3 (https://www.python.org/) or ensure python3 is available.');
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const srcPath = resolvePythonPath();

  const env = { ...process.env };
  if (srcPath) {
    env.PYTHONPATH = env.PYTHONPATH ? `${srcPath}:${env.PYTHONPATH}` : srcPath;
  }

  const child = spawn(pythonBin, ['-m', 'agent_gauntlet.cli', ...args], {
    stdio: 'inherit',
    env: env,
  });

  child.on('error', (err) => {
    console.error(`[agent-gauntlet] Failed to execute agent-gauntlet engine: ${err.message}`);
    process.exit(1);
  });

  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exit(code !== null ? code : 1);
    }
  });
}

main();
