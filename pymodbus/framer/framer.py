"""Framing layer.

The framing layer is responsible for isolating/generating the request/request from
the frame (prefix - postfix)

According to the selected type of modbus frame a prefix/suffix is added/removed

This layer is also responsible for discarding invalid frames and frames for other slaves.
"""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum

from pymodbus.framer.ascii import MessageAscii
from pymodbus.framer.base import MessageBase
from pymodbus.framer.raw import MessageRaw
from pymodbus.framer.rtu import MessageRTU
from pymodbus.framer.socket import MessageSocket
from pymodbus.framer.tls import MessageTLS
from pymodbus.transport.transport import CommParams, ModbusProtocol


class FramerType(str, Enum):
    """Type of Modbus frame."""

    RAW = "raw"  # only used for testing
    ASCII = "ascii"
    RTU = "rtu"
    SOCKET = "socket"
    TLS = "tls"


class Framer(ModbusProtocol):
    """Framing layer extending transport layer.

    extends the ModbusProtocol to handle receiving and sending of complete modbus PDU.

    Framing is the prefix / suffix around the response/request

    When receiving:
    - Secures full valid Modbus PDU is received (across multiple callbacks)
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
            message_type: FramerType,
            params: CommParams,
            is_server: bool,
            device_ids: list[int],
        ):
        """Initialize a message instance.

        :param message_type: Modbus message type
        :param params: parameter dataclass
        :param is_server: true if object act as a server (listen/connect)
        :param device_ids: list of device id to accept, 0 in list means broadcast.
        """
        super().__init__(params, is_server)
        self.device_ids = device_ids
        self.broadcast: bool = (0 in device_ids)
        self.msg_handle: MessageBase = {
            FramerType.RAW: MessageRaw(),
            FramerType.ASCII: MessageAscii(),
            FramerType.RTU: MessageRTU(),
            FramerType.SOCKET: MessageSocket(),
            FramerType.TLS: MessageTLS(),
        }[message_type]


    def validate_device_id(self, dev_id: int) -> bool:
        """Check if device id is expected."""
        return self.broadcast or (dev_id in self.device_ids)


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
