"""Simulator data model implementation.

**REMARK** This code is experimental and not integrated into production.
"""
from __future__ import annotations

from dataclasses import dataclass

from pymodbus.constants import DataType

from .simdata import SimAction, SimData
from .simdevice import SimDevices


class SimRuntimeRegister:
    """Datastore for a single register."""

    FLAG_REG_SIZE_1 = 0       # datatypes with 1 register e.g. INT16, STRING
    FLAG_REG_SIZE_2 = 1       # datatypes with 2 register e.g. INT32
    FLAG_REG_SIZE_4 = 2       # datatypes with 1 register e.g. INT64
    FLAG_REGISTERS = 2**2 -1  # bits 0-1 is datatype size
    FLAG_INVALID = 2**2       # bit 2, neither read nor write is allowed
    FLAG_READONLY = 2**3      # bit 3, only read is allowed
    FLAG_NO_DIRECT = 2**4     # bit 4, part of a Datatype e.g. INT32
    FLAG_ACTION = 2**5        # bit 5, Action defined

    def __init__(self, flags: int, register: int):
        """Do setup register."""
        self.flags = flags
        self.register = register

    def data_size(self) -> int:
        """Get data size."""
        if not (sz := 2 * (self.flags & self.FLAG_REGISTERS)):
            sz = 1
        return sz

    def is_invalid(self) -> bool:
        """Check for invalid."""
        return bool(self.flags & self.FLAG_INVALID)

    def is_readonly(self) -> bool:
        """Check for readonly."""
        return bool(self.flags & self.FLAG_READONLY)

    def is_no_direct(self) -> bool:
        """Check for no direct register."""
        return bool(self.flags & self.FLAG_NO_DIRECT)

    def is_action(self) -> bool:
        """Check for attached action."""
        return bool(self.flags & self.FLAG_ACTION)


@dataclass(order=True)
class SimRuntimeAction:
    """Datastore for a single action."""

    start_address: int
    count: int
    datatype: DataType
    action: SimAction

@dataclass(order=True)
class SimRuntimeDevice:
    """Datastore for a device."""

    device_id: int
    start_address: int
    end_address: int
    registers: list[SimRuntimeRegister]
    actions: list[SimRuntimeAction]
    endian: tuple[str, str]
    type_check: bool
    identity: str
    offset_index: tuple[int, int, int, int] | None


class SimSetupRuntime:
    """Helper class to convert SimData/SimDevice to runtime data."""

    def __init__(self) -> None:
        """Build runtime lists."""

    def build_simdata(self, entry: SimData, default: SimData) -> tuple[list[SimRuntimeRegister], SimRuntimeAction | None]:
        """Convert single SimData."""
        _ = default
        if entry.action:
            action = SimRuntimeAction(entry.address, entry.count, entry.datatype, entry.action)
            return ([], action)
        return ([], None)

    def build_block(self, device: SimRuntimeDevice, listdata: list[SimData], default: SimData):
        """Build register/action arrays."""
        registers: list[SimRuntimeRegister] = []
        actions: list[SimRuntimeAction] = []
        for entry in listdata:
            regs, action = self.build_simdata(entry, default)
            registers.extend(regs)
            if action:
                actions.append(action)
        device.registers = registers
        device.actions = actions

    def build_runtime(self, devices: SimDevices) -> dict[int, SimRuntimeDevice]:
        """Build runtime classes."""
        if not isinstance(devices, SimDevices):
            raise TypeError("Please use devices=<SimDevices>")
        runtime: dict[int, SimRuntimeDevice] = {}
        for device in devices.devices:
            default = device.default if device.default else SimData(0, invalid=True)
            endian = ("big" if device.endian[0] else "little",
                      "big" if device.endian[1] else "little")
            runtime_device = SimRuntimeDevice(
                device_id = device.id,
                start_address = default.address,
                end_address = 0,
                registers = [],
                actions = [],
                endian = endian,
                type_check = device.type_check,
                identity = device.identity,
                offset_index = device.offset_address,
            )
            self.build_block(runtime_device, device.registers, default)
            runtime[device.id] = runtime_device
        return runtime
