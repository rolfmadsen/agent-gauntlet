#!/usr/bin/env node
/**
 * agent-gauntlet CLI bootstrapper for npm / npx.
 * Provides native platform detection, doctor, status, and supervisor diagnostics.
 */

const { spawnSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

function getPlatformInfo() {
  const platform = os.platform();
  const arch = os.arch();
  const isLinux = platform === 'linux';
  const isSupported = isLinux;
  return { platform, arch, isLinux, isSupported };
}

function handleStatus() {
  const info = getPlatformInfo();
  console.log('[agent-gauntlet] Status Overview:');
  console.log(`  Platform: ${info.platform} (${info.arch})`);
  console.log(`  Support Profile: ${info.isSupported ? 'LOCAL_SUPERVISED (Linux)' : 'UNSUPPORTED_HOST'}`);

  if (info.isLinux) {
    const runtimeDir = process.env.XDG_RUNTIME_DIR || path.join(os.homedir(), '.local', 'state');
    const socketPath = path.join(runtimeDir, 'agent-gauntlet', 'supervisor.sock');
    const socketExists = fs.existsSync(socketPath);
    console.log(`  Socket Path: ${socketPath}`);
    console.log(`  Socket Status: ${socketExists ? 'ACTIVE' : 'IDLE / NOT_INITIALIZED'}`);
  } else {
    console.log('  Notice: macOS and Windows native supervisors are planned for a future release (Tasks 036 & 037).');
  }
  process.exit(0);
}

function handleDoctor() {
  const info = getPlatformInfo();
  console.log('[agent-gauntlet] Doctor Diagnostics:');
  console.log(`  [+] Node.js runtime: ${process.version} (>=18.0.0 required)`);

  if (info.isLinux) {
    console.log('  [+] Platform: Linux kernel supported for systemd socket activation.');
    const bwrapCheck = spawnSync('which', ['bwrap'], { stdio: 'ignore' });
    if (bwrapCheck.status === 0) {
      console.log('  [+] Bubblewrap (bwrap): Installed and available for isolated sandboxing.');
    } else {
      console.log('  [*] Bubblewrap (bwrap): Not found on PATH. Subprocess isolation fallback will be used.');
    }
  } else {
    console.log(`  [!] Platform '${info.platform}' is currently not supported for LOCAL_SUPERVISED mode.`);
    console.log('      Native support is planned under Task 036 (macOS launchd) and Task 037 (Windows Service).');
  }
  process.exit(0);
}

function handleUninstall() {
  console.log('[agent-gauntlet] Uninstalling local supervisor integration...');
  const info = getPlatformInfo();
  if (info.isLinux) {
    const configHome = process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config');
    const userSystemd = path.join(configHome, 'systemd', 'user');
    for (const file of ['agent-gauntlet.socket', 'agent-gauntlet.service']) {
      const p = path.join(userSystemd, file);
      if (fs.existsSync(p)) {
        fs.unlinkSync(p);
        console.log(`  [-] Removed ${p}`);
      }
    }
  }
  console.log('[agent-gauntlet] Uninstall completed.');
  process.exit(0);
}

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
      // try next
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
  const args = process.argv.slice(2);
  const command = args[0];

  if (command === 'status') {
    handleStatus();
  }
  if (command === 'doctor') {
    handleDoctor();
  }
  if (command === 'uninstall') {
    handleUninstall();
  }

  const pythonBin = findPythonBinary();
  if (!pythonBin) {
    console.error('[agent-gauntlet] Error: Python 3.10+ was not found on your system PATH.');
    console.error('[agent-gauntlet] Please ensure Python 3 is installed for full verification engine support.');
    process.exit(1);
  }

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
    console.error(`[agent-gauntlet] Failed to execute engine: ${err.message}`);
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
