"""Encapsulated Interface (MEI) Transport Messages."""
from __future__ import annotations

import struct

from pymodbus.constants import DeviceInformation, MoreData
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.device import DeviceInformationFactory, ModbusControlBlock
from pymodbus.pdu.pdu import ModbusExceptions as merror
from pymodbus.pdu.pdu import ModbusPDU


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

    def __init__(self, oid: int) -> None:
        self.oid = oid
        super().__init__()
        self.oid = oid


class ReadDeviceInformationRequest(ModbusPDU):
    """ReadDeviceInformationRequest."""

    function_code = 0x2B
    sub_function_code = 0x0E
    rtu_frame_size = 7

    def __init__(self, read_code=None, object_id=0x00, slave_id=1, transaction_id=0) -> None:
        """Initialize a new instance."""
        super().__init__(transaction_id=transaction_id, slave_id=slave_id)
        self.read_code = read_code or DeviceInformation.BASIC
        self.object_id = object_id

    def encode(self) -> bytes:
        """Encode the request packet."""
        packet = struct.pack(
            ">BBB", self.sub_function_code, self.read_code, self.object_id
        )
        return packet

    def decode(self, data: bytes) -> None:
        """Decode data part of the message."""
        params = struct.unpack(">BBB", data)
        self.sub_function_code, self.read_code, self.object_id = params

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """Run a read exception status request against the store."""
        if not 0x00 <= self.object_id <= 0xFF:
            return self.doException(merror.IllegalValue)
        if not 0x00 <= self.read_code <= 0x04:
            return self.doException(merror.IllegalValue)

        information = DeviceInformationFactory.get(_MCB, self.read_code, self.object_id)
        return ReadDeviceInformationResponse(read_code=self.read_code, information=information, slave_id=self.slave_id, transaction_id=self.transaction_id)


class ReadDeviceInformationResponse(ModbusPDU):
    """ReadDeviceInformationResponse."""

    function_code = 0x2B
    sub_function_code = 0x0E

    @classmethod
    def calculateRtuFrameSize(cls, buffer: bytes) -> int:
        """Calculate the size of the message."""
        size = 8  # skip the header information
        count = int(buffer[7])

        try:
            while count > 0:
                _, object_length = struct.unpack(">BB", buffer[size : size + 2])
                size += object_length + 2
                count -= 1
            return size + 2
        except struct.error as exc:
            raise IndexError from exc

    def __init__(self, read_code=None, information=None, slave_id=1, transaction_id=0) -> None:
        """Initialize a new instance."""
        super().__init__(transaction_id=transaction_id, slave_id=slave_id)
        self.read_code = read_code or DeviceInformation.BASIC
        self.information = information or {}
        self.number_of_objects = 0
        self.conformity = 0x83  # I support everything right now
        self.next_object_id = 0x00
        self.more_follows = MoreData.NOTHING
        self.space_left = 253 - 6

    def _encode_object(self, object_id: int, data: bytes | ModbusPDU) -> bytes:
        """Encode object."""
        if not isinstance(data, bytes):
            data = data.encode()
        data_len = len(data)
        self.space_left -= 2 + data_len
        if self.space_left <= 0:
            raise _OutOfSpaceException(object_id)
        encoded_obj = struct.pack(">BB", object_id, data_len)
        encoded_obj += data
        self.number_of_objects += 1
        return encoded_obj

    def encode(self) -> bytes:
        """Encode the response."""
        packet = struct.pack(
            ">BBB", self.sub_function_code, self.read_code, self.conformity
        )
        objects = b""
        try:
            for object_id, data in iter(self.information.items()):
                if isinstance(data, list):
                    for item in data:
                        objects += self._encode_object(object_id, item)
                else:
                    objects += self._encode_object(object_id, data)
        except _OutOfSpaceException as exc:
            self.next_object_id = exc.oid
            self.more_follows = MoreData.KEEP_READING

        packet += struct.pack(
            ">BBB", self.more_follows, self.next_object_id, self.number_of_objects
        )
        packet += objects
        return packet

    def decode(self, data: bytes) -> None:
        """Decode a the response."""
        params = struct.unpack(">BBBBBB", data[0:6])
        self.sub_function_code, self.read_code = params[0:2]
        self.conformity, self.more_follows = params[2:4]
        self.next_object_id, self.number_of_objects = params[4:6]
        self.information, count = {}, 6  # skip the header information

        while count < len(data):
            object_id, object_length = struct.unpack(">BB", data[count : count + 2])
            count += object_length + 2
            if object_id not in self.information:
                self.information[object_id] = data[count - object_length : count]
            elif isinstance(self.information[object_id], list):
                self.information[object_id].append(data[count - object_length : count])
            else:
                self.information[object_id] = [
                    self.information[object_id],
                    data[count - object_length : count],
                ]
