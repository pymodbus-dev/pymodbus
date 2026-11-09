"""Framer."""

__all__ = [
    "DecodePDU",
    "FileRecord",
    "ModbusControlBlock",
    "ModbusDeviceIdentification",
    "ModbusPdu",
    "PDUexception",
    "StoreGet",
    "StoreSet",
    "add_pdu",
    "pack_bitstring",
    "unpack_bitstring",
]

from .data_message import PDUreadCoils
from .device import ModbusControlBlock, ModbusDeviceIdentification
from .diag_message import PDUdiagnostic
from .other_message import FileRecord, PDUreadExceptionStatus
from .pdu import (
    DecodePDU,
    ModbusPdu,
    PDUexception,
    StoreGet,
    StoreSet,
    pack_bitstring,
    unpack_bitstring,
)


def add_pdu(pdu: type[ModbusPdu]) -> None:
    """Make add_pdu global."""
    DecodePDU.add_pdu(pdu)


_ = PDUreadCoils
_ = PDUdiagnostic
_ = PDUreadExceptionStatus
