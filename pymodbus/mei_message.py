"""Encapsulated Interface (MEI) Transport Messages."""
import struct
from pymodbus.constants import DeviceInformation, MoreData
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.device import ModbusControlBlock
from pymodbus.device import DeviceInformationFactory
from pymodbus.pdu import ModbusExceptions as merror

_MCB = ModbusControlBlock()


class _OutOfSpaceException(Exception):
    """Internal out of space exception."""

    # This exception exists here as a simple, local way to manage response
    # length control for the only MODBUS command which requires it under
    # standard, non-error conditions. It and the structures associated with
    # it should ideally be refactored and applied to all responses, however,
    # since a Client can make requests which result in disallowed conditions,
    # such as, for instance, requesting a register read of more registers
    # than will fit in a single PDU. As per the specification, the PDU is
    # restricted to 253 bytes, irrespective of the transport used.
    #
    # See Page 5/50 of MODBUS Application Protocol Specification V1.1b3.

    def __init__(self, oid):
        self.oid = oid
        super().__init__()


# ---------------------------------------------------------------------------#
#  Read Device Information
# ---------------------------------------------------------------------------#
class ReadDeviceInformationRequest(ModbusRequest):
    """Read device information.

    This function code allows reading the identification and additional
    information relative to the physical and functional description of a
    remote device, only.

    The Read Device Identification interface is modeled as an address space
    composed of a set of addressable data elements. The data elements are
    called objects and an object Id identifies them.
    """

    function_code = 0x2B
    sub_function_code = 0x0E
    _rtu_frame_size = 7

    def __init__(self, read_code=None, object_id=0x00, **kwargs):
        """Initialize a new instance.

        :param read_code: The device information read code
        :param object_id: The object to read from
        """
        ModbusRequest.__init__(self, **kwargs)
        self.read_code = read_code or DeviceInformation.Basic
        self.object_id = object_id

    def encode(self):
        """Encode the request packet.

        :returns: The byte encoded packet
        """
        packet = struct.pack(
            ">BBB", self.sub_function_code, self.read_code, self.object_id
        )
        return packet

    def decode(self, data):
        """Decode data part of the message.

        :param data: The incoming data
        """
        params = struct.unpack(">BBB", data)
        self.sub_function_code, self.read_code, self.object_id = params

    def execute(self, context):  # NOSONAR pylint: disable=unused-argument
        """Run a read exception status request against the store.

        :param context: The datastore to request from
        :returns: The populated response
        """
        if not 0x00 <= self.object_id <= 0xFF:
            return self.doException(merror.IllegalValue)
        if not 0x00 <= self.read_code <= 0x04:
            return self.doException(merror.IllegalValue)

        information = DeviceInformationFactory.get(_MCB, self.read_code, self.object_id)
        return ReadDeviceInformationResponse(self.read_code, information)

    def __str__(self):
        """Build a representation of the request.

        :returns: The string representation of the request
        """
        params = (self.read_code, self.object_id)
        return (
            "ReadDeviceInformationRequest(%d,%d)" % params  # pylint: disable=consider-using-f-string
        )


class ReadDeviceInformationResponse(ModbusResponse):
    """Read device information response."""

    function_code = 0x2B
    sub_function_code = 0x0E

    @classmethod
    def calculateRtuFrameSize(cls, buffer):
        """Calculate the size of the message

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the response.
        """
        size = 8  # skip the header information
        count = int(buffer[7])

        while count > 0:
            _, object_length = struct.unpack(">BB", buffer[size : size + 2])
            size += object_length + 2
            count -= 1
        return size + 2

    def __init__(self, read_code=None, information=None, **kwargs):
        """Initialize a new instance.

        :param read_code: The device information read code
        :param information: The requested information request
        """
        ModbusResponse.__init__(self, **kwargs)
        self.read_code = read_code or DeviceInformation.Basic
        self.information = information or {}
        self.number_of_objects = 0
        self.conformity = 0x83  # I support everything right now
        self.next_object_id = 0x00
        self.more_follows = MoreData.Nothing
        self.space_left = None

    def _encode_object(self, object_id, data):
        """Encode object."""
        self.space_left -= 2 + len(data)
        if self.space_left <= 0:
            raise _OutOfSpaceException(object_id)
        encoded_obj = struct.pack(">BB", object_id, len(data))
        if isinstance(data, bytes):
            encoded_obj += data
        else:
            encoded_obj += data.encode()
        self.number_of_objects += 1
        return encoded_obj

    def encode(self):
        """Encode the response.

        :returns: The byte encoded message
        """
        packet = struct.pack(
            ">BBB", self.sub_function_code, self.read_code, self.conformity
        )
        self.space_left = 253 - 6
        objects = b""
        try:
            for (object_id, data) in iter(self.information.items()):
                if isinstance(data, list):
                    for item in data:
                        objects += self._encode_object(object_id, item)
                else:
                    objects += self._encode_object(object_id, data)
        except _OutOfSpaceException as exc:
            self.next_object_id = exc.oid
            self.more_follows = MoreData.KeepReading

        packet += struct.pack(
            ">BBB", self.more_follows, self.next_object_id, self.number_of_objects
        )
        packet += objects
        return packet

    def decode(self, data):
        """Decode a the response.

        :param data: The packet data to decode
        """
        params = struct.unpack(">BBBBBB", data[0:6])
        self.sub_function_code, self.read_code = params[0:2]
        self.conformity, self.more_follows = params[2:4]
        self.next_object_id, self.number_of_objects = params[4:6]
        self.information, count = {}, 6  # skip the header information

        while count < len(data):
            object_id, object_length = struct.unpack(">BB", data[count : count + 2])
            count += object_length + 2
            if object_id not in self.information.keys():
                self.information[object_id] = data[count - object_length : count]
            elif isinstance(self.information[object_id], list):
                self.information[object_id].append(data[count - object_length : count])
            else:
                self.information[object_id] = [
                    self.information[object_id],
                    data[count - object_length : count],
                ]

    def __str__(self):
        """Build a representation of the response.

        :returns: The string representation of the response
        """
        return f"ReadDeviceInformationResponse({self.read_code})"


# ---------------------------------------------------------------------------#
#  Exported symbols
# ---------------------------------------------------------------------------#
__all__ = [
    "ReadDeviceInformationRequest",
    "ReadDeviceInformationResponse",
]
