"""TLS framer."""

from pymodbus.framer.old_framer_base import ModbusFramer
from pymodbus.framer.tls import FramerTLS


# --------------------------------------------------------------------------- #
# Modbus TLS old framer
# --------------------------------------------------------------------------- #


class ModbusTlsFramer(ModbusFramer):
    """Modbus TLS Frame controller.

    No prefix MBAP header before decrypted PDU is used as a message frame for
    Modbus Security Application Protocol.  It allows us to easily separate
    decrypted messages which is PDU as follows:

        [ Function Code] [ Data ]
          1b               Nb
    """

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder factory implementation to use
        """
        print(client)
        super().__init__(decoder, FramerTLS)
