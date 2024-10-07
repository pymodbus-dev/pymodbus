"""Framer."""
__all__ = [
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
    "FramerBase",
    "FramerType",
    "FramerAscii",
    "FramerRTU",
    "FramerSocket",
    "FramerTLS"
]

from pymodbus.framer.ascii import FramerAscii
from pymodbus.framer.base import FramerBase, FramerType
from pymodbus.framer.old_framer_ascii import ModbusAsciiFramer
from pymodbus.framer.old_framer_base import ModbusFramer
from pymodbus.framer.old_framer_rtu import ModbusRtuFramer
from pymodbus.framer.old_framer_socket import ModbusSocketFramer
from pymodbus.framer.old_framer_tls import ModbusTlsFramer
from pymodbus.framer.rtu import FramerRTU
from pymodbus.framer.socket import FramerSocket
from pymodbus.framer.tls import FramerTLS


FRAMER_NAME_TO_OLD_CLASS = {
    FramerType.ASCII: ModbusAsciiFramer,
    FramerType.RTU: ModbusRtuFramer,
    FramerType.SOCKET: ModbusSocketFramer,
    FramerType.TLS: ModbusTlsFramer,
}
FRAMER_NAME_TO_CLASS = {
    FramerType.ASCII: FramerAscii,
    FramerType.RTU: FramerRTU,
    FramerType.SOCKET: FramerSocket,
    FramerType.TLS: FramerTLS,
}
