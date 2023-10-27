"""Framer."""
__all__ = [
    "Framer",
    "FRAMER_NAME_TO_CLASS",
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusBinaryFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
]


import enum

from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.base import ModbusFramer
from pymodbus.framer.binary_framer import ModbusBinaryFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer


class Framer(str, enum.Enum):
    """These represent the different framers."""

    ASCII = "ascii"
    BINARY = "binary"
    RTU = "rtu"
    SOCKET = "socket"
    TLS = "tls"


FRAMER_NAME_TO_CLASS = {
    Framer.ASCII: ModbusAsciiFramer,
    Framer.BINARY: ModbusBinaryFramer,
    Framer.RTU: ModbusRtuFramer,
    Framer.SOCKET: ModbusSocketFramer,
    Framer.TLS: ModbusTlsFramer,
}
