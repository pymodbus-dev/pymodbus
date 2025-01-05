"""Simulator data model classes."""
from __future__ import annotations

from pymodbus.simulator.simdata import SimDevice


def SimCheckConfig(devices: list[SimDevice]) -> bool:
    """Verify configuration."""
    _ = devices
    return False

class SimCore:  # pylint: disable=too-few-public-methods
    """Datastore for the simulator/server."""
