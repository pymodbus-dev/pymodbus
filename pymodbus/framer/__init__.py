"""Framer."""
__all__ = [
    "Framer",
    "FRAMER_NAME_TO_CLASS",
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
    "Message",
    "MessageType",
]


import enum

from pymodbus.framer.message import Message, MessageType
from pymodbus.framer.old_framer_ascii import ModbusAsciiFramer
from pymodbus.framer.old_framer_base import ModbusFramer
from pymodbus.framer.old_framer_rtu import ModbusRtuFramer
from pymodbus.framer.old_framer_socket import ModbusSocketFramer
from pymodbus.framer.old_framer_tls import ModbusTlsFramer


class Framer(str, enum.Enum):
    """These represent the different framers."""

    ASCII = "ascii"
    RTU = "rtu"
    SOCKET = "socket"
    TLS = "tls"


FRAMER_NAME_TO_CLASS = {
    Framer.ASCII: ModbusAsciiFramer,
    Framer.RTU: ModbusRtuFramer,
    Framer.SOCKET: ModbusSocketFramer,
    Framer.TLS: ModbusTlsFramer,
}
