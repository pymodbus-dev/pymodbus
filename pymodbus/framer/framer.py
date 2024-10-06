"""Framing layer.

The framer layer is responsible for isolating/generating the request/request from
the frame (prefix - postfix)

According to the selected type of modbus frame a prefix/suffix is added/removed

This layer is also responsible for discarding invalid frames and frames for other slaves.
"""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer.ascii import FramerAscii
from pymodbus.framer.rtu import FramerRTU
from pymodbus.framer.socket import FramerSocket
from pymodbus.framer.tls import FramerTLS
from pymodbus.transport.transport import CommParams, ModbusProtocol


class FramerType(str, Enum):
    """Type of Modbus frame."""

    ASCII = "ascii"
    RTU = "rtu"
    SOCKET = "socket"
    TLS = "tls"


class AsyncFramer(ModbusProtocol):
    """Framer layer extending transport layer.

    extends the ModbusProtocol to handle receiving and sending of complete modbus PDU.

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
            framer_type: FramerType,
            params: CommParams,
            is_server: bool,
            decoder: ClientDecoder | ServerDecoder,
            device_ids: list[int],
        ):
        """Initialize a framer instance.

        :param framer_type: Modbus message type
        :param params: parameter dataclass
        :param is_server: true if object act as a server (listen/connect)
        :param device_ids: list of device id to accept, 0 in list means broadcast.
        """
        super().__init__(params, is_server)
        self.device_ids = device_ids
        self.broadcast: bool = (0 in device_ids)

        self.handle = {
            FramerType.ASCII: FramerAscii(decoder, device_ids),
            FramerType.RTU: FramerRTU(decoder, device_ids),
            FramerType.SOCKET: FramerSocket(decoder, device_ids),
            FramerType.TLS: FramerTLS(decoder, device_ids),
        }[framer_type]


    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        tot_len = 0
        buf_len = len(data)
        while True:
            used_len, msg = self.handle.decode(data[tot_len:])
            tot_len += used_len
            if msg:
                if self.broadcast or self.handle.incoming_dev_id in self.device_ids:
                    self.callback_request_response(msg, self.handle.incoming_dev_id, self.handle.incoming_tid)
                if tot_len == buf_len:
                    return tot_len
            else:
                return tot_len

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
        send_data = self.handle.encode(data, device_id, tid)
        self.send(send_data, addr)
