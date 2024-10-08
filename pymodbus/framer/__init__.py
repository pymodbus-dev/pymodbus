"""Framer."""
__all__ = [
    "FramerBase",
    "FramerType",
    "FramerAscii",
    "FramerRTU",
    "FramerSocket",
    "FramerTLS"
]

from pymodbus.framer.ascii import FramerAscii
from pymodbus.framer.base import FramerBase, FramerType
from pymodbus.framer.rtu import FramerRTU
from pymodbus.framer.socket import FramerSocket
from pymodbus.framer.tls import FramerTLS


FRAMER_NAME_TO_CLASS = {
    FramerType.ASCII: FramerAscii,
    FramerType.RTU: FramerRTU,
    FramerType.SOCKET: FramerSocket,
    FramerType.TLS: FramerTLS,
}
