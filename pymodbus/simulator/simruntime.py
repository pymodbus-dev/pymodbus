"""Simulator data model implementation."""
from __future__ import annotations

from dataclasses import dataclass

from .simdata import SimAction, SimData
from .simdevice import SimDevice


FLAG_REGISTERS = 2^8 -1  # bits 0-3 is datatype size
FLAG_INVALID = 2^8       # bit 4, neither read nor write is allowed
FLAG_READONLY = 2^16     # bit 5, only read is allowed
FLAG_NO_DIRECT = 2^32    # bit 6, part of a Datatype e.g. INT32
FLAG_ACTION = 2^64       # bit 7, Action defined

@dataclass(order=True)
class SimRuntimeRegister:
    """Datastore for a single register."""

    flags: int = 0
    register: int = 0

@dataclass(order=True)
class SimRuntimeDefault(SimRuntimeRegister):
    """Datastore for not defined registers."""

    start_address: int = 0
    end_address: int = 0

@dataclass(order=True)
class SimRuntimeAction:
    """Datastore for a single action."""

    start_address: int
    end_address: int
    action: SimAction

@dataclass(order=True)
class SimRuntimeBlock:
    """Datastore for a continuous block of registers."""

    start_address: int
    end_address: int
    registers: list[SimRuntimeRegister]
    actions: list[SimRuntimeAction]

@dataclass(order=True)
class SimRuntimeDevice:
    """Datastore for a device."""

    register_blocks: list[SimRuntimeBlock]
    type_check: bool
    offset_coil: int = 0
    offset_direct: int = 0
    offset_holding: int = 0
    offset_input: int = 0

class SimSetupRuntime:
    """Helper class to convert SimData/SimDevice to runtime data."""

    def __init__(self, devices: list[SimDevice]) -> None:
        """Register SimDevice(s)."""
        self.configDevices = devices
        self.runtimeDevices: dict[int, SimRuntimeDevice] = {}

    def prepare_block(self, _block: list[SimData], _name: str, _device_id: int) -> tuple[list[SimRuntimeBlock], list[SimRuntimeAction]]:
        """Prepare blocks."""
        return ([], [])

    def build_runtime(self):
        """Build runtime classes."""
