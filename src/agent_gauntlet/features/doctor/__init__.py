"""Doctor feature module for agent-gauntlet workspace integrity analysis."""

from agent_gauntlet.features.doctor.checker import DoctorChecker
from agent_gauntlet.features.doctor.models import (
    DoctorFinding,
    DoctorReport,
    FindingSeverity,
)

__all__ = ["DoctorChecker", "DoctorFinding", "DoctorReport", "FindingSeverity"]
