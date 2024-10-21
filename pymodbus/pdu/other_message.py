"""Diagnostic record read/write.

Currently not all implemented
"""


# pylint: disable=missing-type-doc
import struct

from pymodbus.constants import ModbusStatus
from pymodbus.device import DeviceInformationFactory, ModbusControlBlock
from pymodbus.pdu.pdu import ModbusPDU


_MCB = ModbusControlBlock()


# ---------------------------------------------------------------------------#
#  TODO Make these only work on serial # pylint: disable=fixme
# ---------------------------------------------------------------------------#
class ReadExceptionStatusRequest(ModbusPDU):
    """This function code is used to read the contents of eight Exception Status outputs in a remote device.

    The function provides a simple method for
    accessing this information, because the Exception Output references are
    known (no output reference is needed in the function).
    """

    function_code = 0x07
    function_code_name = "read_exception_status"
    _rtu_frame_size = 4

    def __init__(self, slave=None, transaction=0, skip_encode=0):
        """Initialize a new instance."""
        super().__init__()
        super().setData(slave, transaction, skip_encode)

    def encode(self):
        """Encode the message."""
        return b""

    def decode(self, data):
        """Decode data part of the message.

        :param data: The incoming data
        """

    async def update_datastore(self, _context=None):  # pragma: no cover
        """Run a read exception status request against the store.

        :returns: The populated response
        """
        status = _MCB.Counter.summary()
        return ReadExceptionStatusResponse(status)

    def __str__(self):
        """Build a representation of the request."""
        return f"ReadExceptionStatusRequest({self.function_code})"


class ReadExceptionStatusResponse(ModbusPDU):
    """The normal response contains the status of the eight Exception Status outputs.

    The outputs are packed into one data byte, with one bit
    per output. The status of the lowest output reference is contained
    in the least significant bit of the byte.  The contents of the eight
    Exception Status outputs are device specific.
    """

    function_code = 0x07
    _rtu_frame_size = 5

    def __init__(self, status=0x00, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param status: The status response to report
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.status = status if status < 256 else 255

    def encode(self):
        """Encode the response.

        :returns: The byte encoded message
        """
        return struct.pack(">B", self.status)

    def decode(self, data):
        """Decode a the response.

        :param data: The packet data to decode
        """
        self.status = int(data[0])

    def __str__(self):
        """Build a representation of the response."""
        arguments = (self.function_code, self.status)
        return (
            "ReadExceptionStatusResponse(%d, %s)"  # pylint: disable=consider-using-f-string
            % arguments
        )


# Encapsulate interface transport 43, 14
# CANopen general reference 43, 13


# ---------------------------------------------------------------------------#
#  TODO Make these only work on serial # pylint: disable=fixme
# ---------------------------------------------------------------------------#
class GetCommEventCounterRequest(ModbusPDU):
    """This function code is used to get a status word.

    And an event count from the remote device's communication event counter.

    By fetching the current count before and after a series of messages, a
    client can determine whether the messages were handled normally by the
    remote device.

    The device's event counter is incremented once  for each successful
    message completion. It is not incremented for exception responses,
    poll commands, or fetch event counter commands.

    The event counter can be reset by means of the Diagnostics function
    (code 08), with a subfunction of Restart Communications Option
    (code 00 01) or Clear Counters and Diagnostic Register (code 00 0A).
    """

    function_code = 0x0B
    function_code_name = "get_event_counter"
    _rtu_frame_size = 4

    def __init__(self, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance."""
        super().__init__()
        super().setData(slave, transaction, skip_encode)

    def encode(self):
        """Encode the message."""
        return b""

    def decode(self, data):
        """Decode data part of the message.

        :param data: The incoming data
        """

    async def update_datastore(self, _context=None):  # pragma: no cover
        """Run a read exception status request against the store.

        :returns: The populated response
        """
        status = _MCB.Counter.Event
        return GetCommEventCounterResponse(status)

    def __str__(self):
        """Build a representation of the request."""
        return f"GetCommEventCounterRequest({self.function_code})"


class GetCommEventCounterResponse(ModbusPDU):
    """Get comm event counter response.

    The normal response contains a two-byte status word, and a two-byte
    event count. The status word will be all ones (FF FF hex) if a
    previously-issued program command is still being processed by the
    remote device (a busy condition exists). Otherwise, the status word
    will be all zeros.
    """

    function_code = 0x0B
    _rtu_frame_size = 8

    def __init__(self, count=0x0000, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param count: The current event counter value
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.count = count
        self.status = True  # this means we are ready, not waiting

    def encode(self):
        """Encode the response.

        :returns: The byte encoded message
        """
        if self.status:  # pragma: no cover
            ready = ModbusStatus.READY
        else:
            ready = ModbusStatus.WAITING  # pragma: no cover
        return struct.pack(">HH", ready, self.count)

    def decode(self, data):
        """Decode a the response.

        :param data: The packet data to decode
        """
        ready, self.count = struct.unpack(">HH", data)
        self.status = ready == ModbusStatus.READY

    def __str__(self):
        """Build a representation of the response."""
        arguments = (self.function_code, self.count, self.status)
        return (
            "GetCommEventCounterResponse(%d, %d, %d)"  # pylint: disable=consider-using-f-string
            % arguments
        )


# ---------------------------------------------------------------------------#
#  TODO Make these only work on serial # pylint: disable=fixme
# ---------------------------------------------------------------------------#
class GetCommEventLogRequest(ModbusPDU):
    """This function code is used to get a status word.

    Event count, message count, and a field of event bytes from the remote device.

    The status word and event counts are identical  to that returned by
    the Get Communications Event Counter function (11, 0B hex).

    The message counter contains the quantity of  messages processed by the
    remote device since its last restart, clear counters operation, or
    power-up.  This count is identical to that returned by the Diagnostic
    function (code 08), sub-function Return Bus Message Count (code 11,
    0B hex).

    The event bytes field contains 0-64 bytes, with each byte corresponding
    to the status of one MODBUS send or receive operation for the remote
    device.  The remote device enters the events into the field in
    chronological order.  Byte 0 is the most recent event. Each new byte
    flushes the oldest byte from the field.
    """

    function_code = 0x0C
    function_code_name = "get_event_log"
    _rtu_frame_size = 4

    def __init__(self, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance."""
        super().__init__()
        super().setData(slave, transaction, skip_encode)

    def encode(self):
        """Encode the message."""
        return b""

    def decode(self, data):
        """Decode data part of the message.

        :param data: The incoming data
        """

    async def update_datastore(self, _context=None):  # pragma: no cover
        """Run a read exception status request against the store.

        :returns: The populated response
        """
        results = {
            "status": True,
            "message_count": _MCB.Counter.BusMessage,
            "event_count": _MCB.Counter.Event,
            "events": _MCB.getEvents(),
        }
        return GetCommEventLogResponse(**results)

    def __str__(self):
        """Build a representation of the request.

        :returns: The string representation of the request
        """
        return f"GetCommEventLogRequest({self.function_code})"


class GetCommEventLogResponse(ModbusPDU):
    """Get Comm event log response.

    The normal response contains a two-byte status word field,
    a two-byte event count field, a two-byte message count field,
    and a field containing 0-64 bytes of events. A byte count
    field defines the total length of the data in these four field
    """

    function_code = 0x0C
    _rtu_byte_count_pos = 2

    def __init__(self, status=True, message_count=0, event_count=0, events=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param status: The status response to report
        :param message_count: The current message count
        :param event_count: The current event count
        :param events: The collection of events to send
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.status = status
        self.message_count = message_count
        self.event_count = event_count
        self.events = events if events else []

    def encode(self):
        """Encode the response.

        :returns: The byte encoded message
        """
        if self.status:  # pragma: no cover
            ready = ModbusStatus.READY
        else:
            ready = ModbusStatus.WAITING  # pragma: no cover
        packet = struct.pack(">B", 6 + len(self.events))
        packet += struct.pack(">H", ready)
        packet += struct.pack(">HH", self.event_count, self.message_count)
        packet += b"".join(struct.pack(">B", e) for e in self.events)
        return packet

    def decode(self, data):
        """Decode a the response.

        :param data: The packet data to decode
        """
        length = int(data[0])
        status = struct.unpack(">H", data[1:3])[0]
        self.status = status == ModbusStatus.READY
        self.event_count = struct.unpack(">H", data[3:5])[0]
        self.message_count = struct.unpack(">H", data[5:7])[0]

        self.events = []
        for i in range(7, length + 1):
            self.events.append(int(data[i]))

    def __str__(self):
        """Build a representation of the response.

        :returns: The string representation of the response
        """
        arguments = (
            self.function_code,
            self.status,
            self.message_count,
            self.event_count,
        )
        return (
            "GetCommEventLogResponse(%d, %d, %d, %d)"  # pylint: disable=consider-using-f-string
            % arguments
        )


# ---------------------------------------------------------------------------#
#  TODO Make these only work on serial # pylint: disable=fixme
# ---------------------------------------------------------------------------#
class ReportSlaveIdRequest(ModbusPDU):
    """This function code is used to read the description of the type.

    The current status, and other information specific to a remote device.
    """

    function_code = 0x11
    function_code_name = "report_slave_id"
    _rtu_frame_size = 4

    def __init__(self, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param slave: Modbus slave slave ID

        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)

    def encode(self):
        """Encode the message."""
        return b""

    def decode(self, data):
        """Decode data part of the message.

        :param data: The incoming data
        """

    async def update_datastore(self, context=None):  # pragma: no cover
        """Run a report slave id request against the store.

        :returns: The populated response
        """
        report_slave_id_data = None
        if context:
            report_slave_id_data = getattr(context, "reportSlaveIdData", None)
        if not report_slave_id_data:
            information = DeviceInformationFactory.get(_MCB)

            # Support identity values as bytes data and regular str data
            id_data = []
            for v_item in information.values():
                if isinstance(v_item, bytes):
                    id_data.append(v_item)
                else:
                    id_data.append(v_item.encode())

            identifier = b"-".join(id_data)
            identifier = identifier or b"Pymodbus"
            report_slave_id_data = identifier
        return ReportSlaveIdResponse(report_slave_id_data)

    def __str__(self):
        """Build a representation of the request.

        :returns: The string representation of the request
        """
        return f"ReportSlaveIdRequest({self.function_code})"


class ReportSlaveIdResponse(ModbusPDU):
    """Show response.

    The data contents are specific to each type of device.
    """

    function_code = 0x11
    _rtu_byte_count_pos = 2

    def __init__(self, identifier=b"\x00", status=True, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param identifier: The identifier of the slave
        :param status: The status response to report
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.identifier = identifier
        self.status = status
        self.byte_count = None

    def encode(self):
        """Encode the response.

        :returns: The byte encoded message
        """
        if self.status:  # pragma: no cover
            status = ModbusStatus.SLAVE_ON
        else:
            status = ModbusStatus.SLAVE_OFF  # pragma: no cover
        length = len(self.identifier) + 1
        packet = struct.pack(">B", length)
        packet += self.identifier  # we assume it is already encoded
        packet += struct.pack(">B", status)
        return packet

    def decode(self, data):
        """Decode a the response.

        Since the identifier is device dependent, we just return the
        raw value that a user can decode to whatever it should be.

        :param data: The packet data to decode
        """
        self.byte_count = int(data[0])
        self.identifier = data[1 : self.byte_count + 1]
        status = int(data[-1])
        self.status = status == ModbusStatus.SLAVE_ON

    def __str__(self) -> str:
        """Build a representation of the response.

        :returns: The string representation of the response
        """
        return f"ReportSlaveIdResponse({self.function_code}, {self.identifier}, {self.status})"
