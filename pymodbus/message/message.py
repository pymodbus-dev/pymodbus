"""ModbusMessage layer.

The message layer is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum

from pymodbus.message.ascii import MessageAscii
from pymodbus.message.base import MessageBase
from pymodbus.message.raw import MessageRaw
from pymodbus.message.rtu import MessageRTU
from pymodbus.message.socket import MessageSocket
from pymodbus.message.tls import MessageTLS
from pymodbus.transport.transport import CommParams, ModbusProtocol


class MessageType(str, Enum):
    """Type of Modbus frame."""

    RAW = "raw"  # only used for testing
    ASCII = "ascii"
    RTU = "rtu"
    SOCKET = "socket"
    TLS = "tls"


class Message(ModbusProtocol):
    """Message layer extending transport layer.

    extends the ModbusProtocol to handle receiving and sending of complete modbus messsagees.

    Message is the prefix / suffix around the response/request

    When receiving:
    - Secures full valid Modbus message is received (across multiple callbacks)
    - Validates and removes Modbus prefix/suffix (CRC for serial, MBAP for others)
    - Callback with pure request/response
    - Skips invalid messagees
    - Hunt for valid message (RTU type)

    When sending:
    - Add prefix/suffix to request/response (CRC for serial, MBAP for others)
    - Call transport to send

    The class is designed to take care of differences between the modbus message types,
    and provide a neutral interface with pure requests/responses to/from the upper layers.
    """

    def __init__(self,
            message_type: MessageType,
            params: CommParams,
            is_server: bool,
            device_ids: list[int] | None,
        ):
        """Initialize a message instance.

        :param message_type: Modbus message type
        :param params: parameter dataclass
        :param is_server: true if object act as a server (listen/connect)
        :param device_ids: list of device id to accept (server only), None for all.
        """
        super().__init__(params, is_server)
        self.device_ids = device_ids
        self.message_type = message_type
        self.msg_handle: MessageBase = {
            MessageType.RAW: MessageRaw(device_ids, is_server),
            MessageType.ASCII: MessageAscii(device_ids, is_server),
            MessageType.RTU: MessageRTU(device_ids, is_server),
            MessageType.SOCKET: MessageSocket(device_ids, is_server),
            MessageType.TLS: MessageTLS(device_ids, is_server),
        }[message_type]

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        tot_len = len(data)
        start = 0
        while True:
            used_len, tid, device_id, msg = self.msg_handle.decode(data[start:])
            if msg:
                self.callback_request_response(msg, device_id, tid)
            if not used_len:
                return start
            start += used_len
            if start == tot_len:
                return tot_len

    # --------------------- #
    # callbacks and helpers #
    # --------------------- #
    @abstractmethod
    def callback_request_response(self, data: bytes, device_id: int, tid: int) -> None:
        """Handle received modbus request/response."""

    def build_send(self, data: bytes, device_id: int, tid: int, addr: tuple | None = None) -> None:
        """Send request/response.

        :param data: non-empty bytes object with data to send.
        :param device_id: device identifier (slave/unit)
        :param tid: transaction id (0 if not used).
        :param addr: optional addr, only used for UDP server.
        """
        send_data = self.msg_handle.encode(data, device_id, tid)
        self.send(send_data, addr)
