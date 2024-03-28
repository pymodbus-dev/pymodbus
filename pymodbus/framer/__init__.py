"""Framer."""
__all__ = [
    "Framer",
    "FRAMER_NAME_TO_CLASS",
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
]


import enum

from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.base import ModbusFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer


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
