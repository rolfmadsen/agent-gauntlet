"""Aggregate test suite for supervisor core, contracts, FSM, WASM policy, keys, engine, sandbox, service, IPC, shim, bootstrapper, offline verifier, and E2E."""

import unittest

from tests.features.supervisor.test_antigravity_shim import TestAntigravityHookShim
from tests.features.supervisor.test_bootstrapper import TestNodeBootstrapper
from tests.features.supervisor.test_contracts import TestSupervisorContracts
from tests.features.supervisor.test_e2e_linux import TestLinuxSupervisorE2E
from tests.features.supervisor.test_engine import TestSupervisorEngine
from tests.features.supervisor.test_event_log import TestSessionEventLog
from tests.features.supervisor.test_fsm import TestSessionFsm
from tests.features.supervisor.test_ipc import TestUnixDomainSocketTransport
from tests.features.supervisor.test_key_provider import TestLinuxKeyProvider
from tests.features.supervisor.test_offline_verifier import TestOfflineReportVerifier
from tests.features.supervisor.test_sandbox import TestBubblewrapSandboxRunner
from tests.features.supervisor.test_seams import TestPlatformSeams
from tests.features.supervisor.test_server import TestSupervisorServer
from tests.features.supervisor.test_service import TestSystemdServiceManager
from tests.features.supervisor.test_snapshot import TestPortableSnapshot
from tests.features.supervisor.test_wasm_policy import TestWasmPolicyVerifier

__all__ = [
    "TestSupervisorContracts",
    "TestSessionFsm",
    "TestPlatformSeams",
    "TestPortableSnapshot",
    "TestWasmPolicyVerifier",
    "TestLinuxKeyProvider",
    "TestSessionEventLog",
    "TestSupervisorEngine",
    "TestSupervisorServer",
    "TestBubblewrapSandboxRunner",
    "TestSystemdServiceManager",
    "TestUnixDomainSocketTransport",
    "TestAntigravityHookShim",
    "TestNodeBootstrapper",
    "TestOfflineReportVerifier",
    "TestLinuxSupervisorE2E",
]

if __name__ == "__main__":
    unittest.main()
