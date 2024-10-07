"""Ascii_framer."""
from pymodbus.framer.old_framer_base import BYTE_ORDER, FRAME_HEADER, ModbusFramer

from .ascii import FramerAscii


ASCII_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER


# --------------------------------------------------------------------------- #
# Modbus ASCII olf framer
# --------------------------------------------------------------------------- #
class ModbusAsciiFramer(ModbusFramer):
    r"""Modbus ASCII Frame Controller.

        [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
          1c        2c         2c         Nc     2c      2c

        * data can be 0 - 2x252 chars
        * end is "\\r\\n" (Carriage return line feed), however the line feed
          character can be changed via a special command
        * start is ":"

    This framer is used for serial transmission.  Unlike the RTU protocol,
    the data in this framer is transferred in plain text ascii.
    """

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        print(client)
        super().__init__(decoder, FramerAscii)
