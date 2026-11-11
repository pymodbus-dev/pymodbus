"""Modbus Device Controller.

These are the device management handlers.  They should be
maintained in the server context and the various methods
should be inserted in the correct locations.
"""

from __future__ import annotations

import struct
from abc import ABC, abstractmethod

from ..constants import DeviceInformation
from ..exceptions import ParameterException
from ..utilities import dict_property
from .pdu import pack_bitstring, unpack_bitstring


# ---------------------------------------------------------------------------#
#  Modbus Event
#
# An event byte returned by the Get Communications Event Log function
# can be any one of four types. The type is defined by bit 7
# (the high-order bit) in each byte. It may be further defined by bit 6.
# ---------------------------------------------------------------------------#
class ModbusEvent(ABC):
    """Define modbus events."""

    @abstractmethod
    def encode(self) -> bytes:
        """Encode the status bits to an event message."""

    @abstractmethod
    def decode(self, event):
        """Decode the event message to its status bits."""


class RemoteReceiveEvent(ModbusEvent):
    """Remote device MODBUS Receive Event.

    The remote device stores this type of event byte when a query message
    is received. It is stored before the remote device processes the message.
    This event is defined by bit 7 set to logic "1". The other bits will be
    set to a logic "1" if the corresponding condition is TRUE. The bit layout
    is::

        Bit Contents
        ----------------------------------
        0   Not Used
        2   Not Used
        3   Not Used
        4   Character Overrun
        5   Currently in Listen Only Mode
        6   Broadcast Receive
        7   1
    """

    def __init__(self, overrun=False, listen=False, broadcast=False):
        """Initialize a new event instance."""
        self.overrun = overrun
        self.listen = listen
        self.broadcast = broadcast

    def encode(self) -> bytes:
        """Encode the status bits to an event message."""
        bits = [False] * 3
        bits += [self.overrun, self.listen, self.broadcast, True]
        packet = pack_bitstring(bits)
        return packet

    def decode(self, event: bytes) -> None:
        """Decode the event message to its status bits."""
        bits = unpack_bitstring(event)
        self.overrun = bits[4]
        self.listen = bits[5]
        self.broadcast = bits[6]


class RemoteSendEvent(ModbusEvent):
    """Remote device MODBUS Send Event.

    The remote device stores this type of event byte when it finishes
    processing a request message. It is stored if the remote device
    returned a normal or exception response, or no response.

    This event is defined by bit 7 set to a logic "0", with bit 6 set to a "1".
    The other bits will be set to a logic "1" if the corresponding
    condition is TRUE. The bit layout is::

        Bit Contents
        -----------------------------------------------------------
        0   Read Exception Sent (Exception Codes 1-3)
        1   Device Abort Exception Sent (Exception Code 4)
        2   Device Busy Exception Sent (Exception Codes 5-6)
        3   Device Program NAK Exception Sent (Exception Code 7)
        4   Write Timeout Error Occurred
        5   Currently in Listen Only Mode
        6   1
        7   0
    """

    def __init__(
        self,
        read=False,
        device_abort=False,
        device_busy=False,
        device_nak=False,
        write_timeout=False,
        listen=False,
    ):
        """Initialize a new event instance."""
        self.read = read
        self.device_abort = device_abort
        self.device_busy = device_busy
        self.device_nak = device_nak
        self.write_timeout = write_timeout
        self.listen = listen

    def encode(self):
        """Encode the status bits to an event message."""
        bits = [
            self.read,
            self.device_abort,
            self.device_busy,
            self.device_nak,
            self.write_timeout,
            self.listen,
        ]
        bits += [True, False]
        packet = pack_bitstring(bits)
        return packet

    def decode(self, event):
        """Decode the event message to its status bits."""
        bits = unpack_bitstring(event)
        self.read = bits[0]
        self.device_abort = bits[1]
        self.device_busy = bits[2]
        self.device_nak = bits[3]
        self.write_timeout = bits[4]
        self.listen = bits[5]


class EnteredListenModeEvent(ModbusEvent):
    """Enter Remote device Listen Only Mode.

    The remote device stores this type of event byte when it enters
    the Listen Only Mode. The event is defined by a content of 04 hex.
    """

    value = 0x04
    __encoded = b"\x04"

    def encode(self):
        """Encode the status bits to an event message."""
        return self.__encoded

    def decode(self, event):
        """Decode the event message to its status bits."""
        if event != self.__encoded:
            raise ParameterException("Invalid decoded value")


class CommunicationRestartEvent(ModbusEvent):
    """Restart remote device Initiated Communication.

    The remote device stores this type of event byte when its communications
    port is restarted. The remote device can be restarted by the Diagnostics
    function (code 08), with sub-function Restart Communications Option
    (code 00 01).

    That function also places the remote device into a "Continue on Error"
    or "Stop on Error" mode. If the remote device is placed  into "Continue on
    Error" mode, the event byte is added to the existing event log. If the
    remote device is placed into "Stop on Error" mode, the byte is added to
    the log and the rest of the log is cleared to zeros.

    The event is defined by a content of zero.
    """

    value = 0x00
    __encoded = b"\x00"

    def encode(self):
        """Encode the status bits to an event message."""
        return self.__encoded

    def decode(self, event):
        """Decode the event message to its status bits."""
        if event != self.__encoded:
            raise ParameterException("Invalid decoded value")


# ---------------------------------------------------------------------------#
#  Modbus Plus Statistics
# ---------------------------------------------------------------------------#
class ModbusPlusStatistics:
    """This is used to maintain the current modbus plus statistics count.

    As of right now this is simply a stub to complete the modbus implementation.
    For more information, see the modbus implementation guide page 87.
    """

    stat_data: dict[str, list[int]] = {
        "node_type_id": [0x00] * 2,  # 00
        "software_version_number": [0x00] * 2,  # 01
        "network_address": [0x00] * 2,  # 02
        "mac_state_variable": [0x00] * 2,  # 03
        "peer_status_code": [0x00] * 2,  # 04
        "token_pass_counter": [0x00] * 2,  # 05
        "token_rotation_time": [0x00] * 2,  # 06
        "program_master_token_failed": [0x00],  # 07 hi
        "data_master_token_failed": [0x00],  # 07 lo
        "program_master_token_owner": [0x00],  # 08 hi
        "data_master_token_owner": [0x00],  # 08 lo
        "program_id_token_owner": [0x00],  # 09 hi
        "data_id_token_owner": [0x00],  # 09 lo
        "data_id_command_transfer": [0x00],  # 10 hi
        "__unused_10_lowbit": [0x00],  # 10 lo
        "program_id_command_transfer": [0x00],  # 11 hi
        "program_master_rsp_transfer": [0x00],  # 11 lo
        "program_id_auto_logout": [0x00],  # 12 hi
        "program_master_connect_status": [0x00],  # 12 lo
        "receive_buffer_dma_overrun": [0x00],  # 13 hi
        "pretransmit_deferral_error": [0x00],  # 13 lo
        "frame_size_error": [0x00],  # 14 hi
        "repeated_command_received": [0x00],  # 14 lo
        "receiver_alignment_error": [0x00],  # 15 hi
        "receiver_collision_abort_error": [0x00],  # 15 lo
        "bad_packet_length_error": [0x00],  # 16 hi
        "receiver_crc_error": [0x00],  # 16 lo
        "transmit_buffer_dma_underrun": [0x00],  # 17 hi
        "bad_link_address_error": [0x00],  # 17 lo
        "bad_mac_function_code_error": [0x00],  # 18 hi
        "internal_packet_length_error": [0x00],  # 18 lo
        "communication_failed_error": [0x00],  # 19 hi
        "communication_retries": [0x00],  # 19 lo
        "no_response_error": [0x00],  # 20 hi
        "good_receive_packet": [0x00],  # 20 lo
        "unexpected_path_error": [0x00],  # 21 hi
        "exception_response_error": [0x00],  # 21 lo
        "forgotten_transaction_error": [0x00],  # 22 hi
        "unexpected_response_error": [0x00],  # 22 lo
        "active_station_bit_map": [0x00] * 8,  # 23-26
        "token_station_bit_map": [0x00] * 8,  # 27-30
        "global_data_bit_map": [0x00] * 8,  # 31-34
        "receive_buffer_use_bit_map": [0x00] * 8,  # 35-37
        "data_master_output_path": [0x00] * 8,  # 38-41
        "data_id_input_path": [0x00] * 8,  # 42-45
        "program_master_outptu_path": [0x00] * 8,  # 46-49
        "program_id_input_path": [0x00] * 8,  # 50-53
    }

    def __init__(self) -> None:
        """Initialize the modbus plus statistics with the default information."""
        self.reset()

    def __iter__(self):
        """Iterate over the statistics."""
        return iter(self.stat_data.items())

    def reset(self) -> None:
        """Clear all of the modbus plus statistics."""
        for key in self.stat_data:
            self.stat_data[key] = [0x00] * len(self.stat_data[key])

    def summary(self):
        """Return a summary of the modbus plus statistics."""
        return iter(self.stat_data.values())

    def encode(self) -> list[int]:
        """Return a summary of the modbus plus statistics."""
        values = [v for sublist in self.stat_data.values() for v in sublist]
        total = [(values[i] << 8) | values[i + 1] for i in range(0, len(values), 2)]
        return total


# ---------------------------------------------------------------------------#
#  Device Information Control
# ---------------------------------------------------------------------------#
class ModbusDeviceIdentification:
    """This is used to supply the device identification.

    For the readDeviceIdentification function

    For more information read section 6.21 of the modbus
    application protocol.
    """

    stat_data = {
        0x00: "",  # VendorName
        0x01: "",  # ProductCode
        0x02: "",  # MajorMinorRevision
        0x03: "",  # VendorUrl
        0x04: "",  # ProductName
        0x05: "",  # ModelName
        0x06: "",  # UserApplicationName
        0x07: "",  # reserved
        0x08: "",  # reserved
        # 0x80 -> 0xFF are private
    }

    __names = [
        "VendorName",
        "ProductCode",
        "MajorMinorRevision",
        "VendorUrl",
        "ProductName",
        "ModelName",
        "UserApplicationName",
    ]

    def __init__(self, info=None, info_name=None):
        """Initialize the datastore with the elements you need."""
        self.stat_data = dict(self.stat_data)
        if isinstance(info_name, dict):
            for key in info_name:
                inx = self.__names.index(key)
                self.stat_data[inx] = info_name[key]

        if isinstance(info, dict):
            for key in info:
                if (0x06 >= key >= 0x00) or (0xFF >= key >= 0x80):
                    self.stat_data[key] = info[key]

    def __iter__(self):
        """Iterate over the device information."""
        return iter(self.stat_data.items())

    def summary(self):
        """Return a summary of the main items."""
        return dict(zip(self.__names, iter(self.stat_data.values())))

    def update(self, value):
        """Update the values of this identity."""
        self.stat_data.update(value)

    def __setitem__(self, key, value):
        """Access the device information."""
        if key not in [0x07, 0x08]:
            self.stat_data[key] = value

    def __getitem__(self, key):
        """Access the device information."""
        return self.stat_data.get(key, "")

    def __str__(self):
        """Build a representation of the device."""
        return "DeviceIdentity"

    # -------------------------------------------------------------------------#
    #  Properties
    # -------------------------------------------------------------------------#
    # fmt: off
    VendorName = dict_property(lambda s: s.stat_data, 0)
    ProductCode = dict_property(lambda s: s.stat_data, 1)
    MajorMinorRevision = dict_property(lambda s: s.stat_data, 2)
    VendorUrl = dict_property(lambda s: s.stat_data, 3)
    ProductName = dict_property(lambda s: s.stat_data, 4)
    ModelName = dict_property(lambda s: s.stat_data, 5)
    UserApplicationName = dict_property(lambda s: s.stat_data, 6)
    # fmt: on


class DeviceInformationFactory:  # pylint: disable=too-few-public-methods
    """This is a helper.

    That really just hides
    some of the complexity of processing the device information
    requests (function code 0x2b 0x0e).
    """

    __lookup = {
        DeviceInformation.BASIC: lambda c, r, i: c.__gets(  # pylint: disable=protected-access
            r, list(range(i, 0x03))
        ),
        DeviceInformation.REGULAR: lambda c, r, i: c.__gets(  # pylint: disable=protected-access
            r,
            list(range(i, 0x07))
            if c.__get(r, i)[i]  # pylint: disable=protected-access
            else list(range(0, 0x07)),
        ),
        DeviceInformation.EXTENDED: lambda c, r, i: c.__gets(  # pylint: disable=protected-access
            r,
            [x for x in range(i, 0x100) if x not in range(0x07, 0x80)]
            if c.__get(r, i)[i]  # pylint: disable=protected-access
            else [x for x in range(0, 0x100) if x not in range(0x07, 0x80)],
        ),
        DeviceInformation.SPECIFIC: lambda c, r, i: c.__get(  # pylint: disable=protected-access
            r, i
        ),
    }

    @classmethod
    def get(cls, control, read_code=DeviceInformation.BASIC, object_id=0x00):
        """Get the requested device data from the system."""
        identity = control.Identity
        return cls.__lookup[read_code](cls, identity, object_id)

    @classmethod
    def __get(cls, identity, object_id):  # pylint: disable=unused-private-member
        """Read a single object_id from the device information."""
        return {object_id: identity[object_id]}

    @classmethod
    def __gets(cls, identity, object_ids):  # pylint: disable=unused-private-member
        """Read multiple object_ids from the device information."""
        return {oid: identity[oid] for oid in object_ids if identity[oid]}


# ---------------------------------------------------------------------------#
#  Counters Handler
# ---------------------------------------------------------------------------#
class ModbusCountersHandler:
    """This is a helper class to simplify the properties for the counters.

    0x0B  1  Return Bus Message Count

             Quantity of messages that the remote
             device has detected on the communications system since its
             last restart, clear counters operation, or power-up.  Messages
             with bad CRC are not taken into account.

    0x0C  2  Return Bus Communication Error Count

             Quantity of CRC errors encountered by the remote device since its
             last restart, clear counters operation, or power-up.  In case of
             an error detected on the character level, (overrun, parity error),
             or in case of a message length < 3 bytes, the receiving device is
             not able to calculate the CRC. In such cases, this counter is
             also incremented.

    0x0D  3  Return device Exception Error Count

             Quantity of MODBUS exception error detected by the remote device
             since its last restart, clear counters operation, or power-up.
             Exception errors are described and listed in "MODBUS Application
             Protocol Specification" document.

    0xOE  4  Return device Message Count

             Quantity of messages addressed to the remote device that the remote
             device has processed since its last restart, clear counters operation,
             or power-up.

    0x0F  5  Return device No Response Count

             Quantity of messages received by the remote device for which it
             returned no response (neither a normal response nor an exception
             response), since its last restart, clear counters operation, or
             power-up.

    0x10  6  Return device NAK Count

             Quantity of messages addressed to the remote device for which it
             returned a Negative ACKNOWLEDGE (NAK) exception response, since
             its last restart, clear counters operation, or power-up. Exception
             responses are described and listed in "MODBUS Application Protocol
             Specification" document.

    0x11  7  Return device Busy Count

             Quantity of messages addressed to the remote device for which it
             returned a device Device Busy exception response, since its last
             restart, clear counters operation, or power-up. Exception
             responses are described and listed in "MODBUS Application
             Protocol Specification" document.

    0x12  8  Return Bus Character Overrun Count

             Quantity of messages addressed to the remote device that it could
             not handle due to a character overrun condition, since its last
             restart, clear counters operation, or power-up. A character
             overrun is caused by data characters arriving at the port faster
             than they can.

    .. note:: I threw the event counter in here for convenience
    """

    stat_data = dict.fromkeys(range(9), 0x00)
    __names = [
        "BusMessage",
        "BusCommunicationError",
        "DeviceExceptionError",
        "DeviceMessage",
        "DeviceNoResponse",
        "DeviceeNAK",
        "DEVICE_BUSY",
        "BusCharacterOverrun",
    ]

    def __iter__(self):
        """Iterate over the device counters."""
        return zip(self.__names, iter(self.stat_data.values()))

    def update(self, values):
        """Update the values of this identity."""
        for k, v_item in iter(values.items()):
            v_item += self.__getattribute__(  # pylint: disable=unnecessary-dunder-call
                k
            )
            self.__setattr__(k, v_item)  # pylint: disable=unnecessary-dunder-call

    def reset(self):
        """Clear all of the system counters."""
        self.stat_data = dict.fromkeys(range(9), 0x00)

    def summary(self):
        """Return a summary of the counters current status."""
        count, result = 0x01, 0x00
        for i in iter(self.stat_data.values()):
            if i != 0x00:  # pylint: disable=compare-to-zero
                result |= count
            count <<= 1
        return result

    # -------------------------------------------------------------------------#
    #  Properties
    # -------------------------------------------------------------------------#
    # fmt: off
    BusMessage = dict_property(lambda s: s.stat_data, 0)
    BusCommunicationError = dict_property(lambda s: s.stat_data, 1)
    BusExceptionError = dict_property(lambda s: s.stat_data, 2)
    DeviceMessage = dict_property(lambda s: s.stat_data, 3)
    DeviceNoResponse = dict_property(lambda s: s.stat_data, 4)
    DeviceNAK = dict_property(lambda s: s.stat_data, 5)
    DEVICE_BUSY = dict_property(lambda s: s.stat_data, 6)
    BusCharacterOverrun = dict_property(lambda s: s.stat_data, 7)
    Event = dict_property(lambda s: s.stat_data, 8)
    # fmt: on


# ---------------------------------------------------------------------------#
#  Main server control block
# ---------------------------------------------------------------------------#
class ModbusControlBlock:
    """This is a global singleton that controls all system information.

    All activity should be logged here and all diagnostic requests
    should come from here.
    """

    _mode = "ASCII"
    _diagnostic = [False] * 16
    _listen_only = False
    _delimiter = b"\n"
    _counters = ModbusCountersHandler()
    _identity = ModbusDeviceIdentification()
    _plus = ModbusPlusStatistics()
    _events: list[ModbusEvent] = []

    _inst: ModbusControlBlock | None = None

    # -------------------------------------------------------------------------#
    #  Magic
    # -------------------------------------------------------------------------#
    def __str__(self):
        """Build a representation of the control block."""
        return "ModbusControl"

    def __iter__(self):
        """Iterate over the device counters."""
        return self._counters.__iter__()

    def __new__(cls):
        """Create a new instance."""
        if cls._inst is None:
            cls._inst = object.__new__(cls)
        return cls._inst

    # -------------------------------------------------------------------------#
    #  Events
    # -------------------------------------------------------------------------#
    def addEvent(self, event: ModbusEvent):
        """Add a new event to the event log."""
        self._events.insert(0, event)
        self._events = self._events[0:64]  # chomp to 64 entries
        self.Counter.Event += 1

    def getEvents(self):
        """Return an encoded collection of the event log."""
        events = [event.encode() for event in self._events]
        return b"".join(events)

    def clearEvents(self):
        """Clear the current list of events."""
        self._events = []

    # -------------------------------------------------------------------------#
    #  Other Properties
    # -------------------------------------------------------------------------#
    Identity = property(lambda s: s._identity)
    Counter = property(lambda s: s._counters)
    Events = property(lambda s: s._events)
    Plus = property(lambda s: s._plus)

    def reset(self):
        """Clear all of the system counters and the diagnostic register."""
        self._events = []
        self._counters.reset()
        self._diagnostic = [False] * 16

    # -------------------------------------------------------------------------#
    #  Listen Properties
    # -------------------------------------------------------------------------#
    def _setListenOnly(self, value):
        """Toggle the listen only status."""
        self._listen_only = bool(value)

    ListenOnly = property(lambda s: s._listen_only, _setListenOnly)

    # -------------------------------------------------------------------------#
    #  Mode Properties
    # -------------------------------------------------------------------------#
    def _setMode(self, mode):
        """Toggle the current serial mode."""
        if mode in {"ASCII", "RTU"}:
            self._mode = mode

    Mode = property(lambda s: s._mode, _setMode)

    # -------------------------------------------------------------------------#
    #  Delimiter Properties
    # -------------------------------------------------------------------------#
    def _setDelimiter(self, char):
        """Change the serial delimiter character."""
        if isinstance(char, str):
            self._delimiter = char.encode()
        if isinstance(char, bytes):
            self._delimiter = char
        elif isinstance(char, int):
            self._delimiter = struct.pack(">B", char)

    Delimiter = property(lambda s: s._delimiter, _setDelimiter)

    # -------------------------------------------------------------------------#
    #  Diagnostic Properties
    # -------------------------------------------------------------------------#
    def setDiagnostic(self, mapping):
        """Set the value in the diagnostic register."""
        for entry in iter(mapping.items()):
            self._diagnostic[entry[0]] = bool(entry[1])

    def getDiagnostic(self, bit):
        """Get the value in the diagnostic register."""
        try:
            if bit and 0 <= bit < len(self._diagnostic):
                return self._diagnostic[bit]
        except Exception:  # pylint: disable=broad-except
            return None
        return None

    def getDiagnosticRegister(self):
        """Get the entire diagnostic register."""
        return self._diagnostic
