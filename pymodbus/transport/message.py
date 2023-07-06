"""ModbusMessage layer.

is extending ModbusTransport to handle receiving and sending of messsagees.

ModbusMessage provides a unified interface to send/receive Modbus requests/responses.
"""
from enum import Enum

from pymodbus.logging import Log
from pymodbus.transport.transport import CommParams, ModbusProtocol


class CommFrameType(Enum):
    """Type of Modbus header"""

    SOCKET = 1
    TLS = 2
    RTU = 3
    ASCII = 4


class ModbusMessage(ModbusProtocol):
    """Message layer extending transport layer.

    When receiving:
    - Secures full valid Modbus message is received (across multiple callbacks from transport)
    - Validates and removes Modbus header (CRC for serial, MBAP for others)
    - Decodes frame according to frame type
    - Callback with pure request/response

    When sending:
    - Encod request/response according to frame type
    - Generate Modbus message by adding header (CRC for serial, MBAP for others)
    - Call transport to do the actual sending of data

    The class is designed to take care of differences between the different modbus headers, and
    provide a neutral interface for the upper layers.
    """

    def __init__(
        self,
        frameType: CommFrameType,
        params: CommParams,
        is_server: bool,
        slaves: list[int],
        function_codes: list[int],
    ) -> None:
        """Initialize a message instance.

        :param frameType: Modbus frame type
        :param params: parameter dataclass
        :param is_server: true if object act as a server (listen/connect)
        :param slaves: list of slave id to accept
        :param function_codes: List of acceptable function codes
        """
        self.slaves = slaves
        self.framerType: ModbusFrameType = {
            CommFrameType.SOCKET: FrameTypeSocket(self),
            CommFrameType.TLS: FrameTypeTLS(self),
            CommFrameType.RTU: FrameTypeRTU(self),
            CommFrameType.ASCII: FrameTypeASCII(self),
        }[frameType]
        self.function_codes = function_codes
        params.new_connection_class = lambda: ModbusMessage(
            frameType,
            self.comm_params,
            False,
            self.slaves,
            self.function_codes,
        )
        super().__init__(params, is_server)

    def callback_data(self, data: bytes, addr: tuple = None) -> int:
        """Handle call from transport with data."""
        if len(data) < self.framerType.min_len:
            return 0

        cut_len = self.framerType.verifyFrameHeader(data)
        if cut_len:
            return cut_len

        # add generic handling
        return 0

    # --------- #
    # callbacks #
    # --------- #
    def callback_message(self, data: bytes) -> None:
        """Handle received data."""
        Log.debug("callback_message called: {}", data, ":hex")

    # ----------------------------------- #
    # Helper methods for external classes #
    # ----------------------------------- #
    def message_send(self, data: bytes, addr: tuple = None) -> None:
        """Send request.

        :param data: non-empty bytes object with data to send.
        :param addr: optional addr, only used for UDP server.
        """
        Log.debug("send: {}", data, ":hex")
        self.transport_send(data, addr=addr)

    # ---------------- #
    # Internal methods #
    # ---------------- #


class ModbusFrameType:  # pylint: disable=too-few-public-methods
    """Generic header"""

    min_len: int = 0


class FrameTypeSocket(ModbusFrameType):  # pylint: disable=too-few-public-methods
    """Modbus Socket frame type.

    [         MBAP Header         ] [ Function Code] [ Data ]
    [ tid ][ pid ][ length ][ uid ]
      2b     2b     2b        1b           1b           Nb

    * length = uid + function code + data
    """

    min_len: int = 8

    def __init__(self, message):
        """Initialize"""
        self.message = message


class FrameTypeTLS(ModbusFrameType):  # pylint: disable=too-few-public-methods
    """Modbus TLS frame type

    [ Function Code] [ Data ]
      1b               Nb
    """

    min_len: int = 1

    def __init__(self, message):
        """Initialize"""
        self.message = message


class FrameTypeRTU(ModbusFrameType):  # pylint: disable=too-few-public-methods
    """Modbus RTU frame type.

    [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ][  End Wait  ]
        3.5 chars     1b         1b               Nb      2b      3.5 chars

    Wait refers to the amount of time required to transmit at least x many
    characters.  In this case it is 3.5 characters.  Also, if we receive a
    wait of 1.5 characters at any point, we must trigger an error message.
    Also, it appears as though this message is little endian. The logic is
    simplified as the following::

    The following table is a listing of the baud wait times for the specified
    baud rates::

        ------------------------------------------------------------------
           Baud  1.5c (18 bits)   3.5c (38 bits)
        ------------------------------------------------------------------
           1200  15,000 ms        31,667 ms
           4800   3,750 ms         7,917 ms
           9600   1,875 ms         3,958 ms
          19200   0,938 ms         1,979 ms
          38400   0,469 ms         0,989 ms
         115200   0,156 ms         0,329 ms
        ------------------------------------------------------------------
        1 Byte = 8 bits + 1 bit parity + 2 stop bit = 11 bits

    * Note: due to the USB converter and the OS drivers, timing cannot be quaranteed
    neither when receiving nor when sending.
    """

    min_len: int = 4

    def __init__(self, message):
        """Initialize"""
        self.message = message


class FrameTypeASCII(ModbusFrameType):  # pylint: disable=too-few-public-methods
    """Modbus ASCII Frame Controller.

    [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
      1c        2c         2c         Nc     2c      2c

    * data can be 0 - 2x252 ASCII chars
    * end is Carriage and return line feed, however the line feed
      character can be changed via a special command
    * start is ":"
    """

    min_len: int = 9

    def __init__(self, message):
        """Initialize"""
        self.message = message
