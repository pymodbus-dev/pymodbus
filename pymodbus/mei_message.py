'''
Encapsulated Interface (MEI) Transport Messages
-----------------------------------------------

'''
import struct
from pymodbus.constants import DeviceInformation, MoreData
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.device import ModbusControlBlock
from pymodbus.device import DeviceInformationFactory
from pymodbus.pdu import ModbusExceptions as merror

_MCB = ModbusControlBlock()


#---------------------------------------------------------------------------#
# Read Device Information
#---------------------------------------------------------------------------#
class ReadDeviceInformationRequest(ModbusRequest):
    '''
    This function code allows reading the identification and additional
    information relative to the physical and functional description of a
    remote device, only.

    The Read Device Identification interface is modeled as an address space
    composed of a set of addressable data elements. The data elements are
    called objects and an object Id identifies them.  
    '''
    function_code = 0x2b
    sub_function_code = 0x0e
    _rtu_frame_size = 3

    def __init__(self, read_code=None, object_id=0x00, **kwargs):
        ''' Initializes a new instance

        :param read_code: The device information read code
        :param object_id: The object to read from
        '''
        ModbusRequest.__init__(self, **kwargs)
        self.read_code = read_code or DeviceInformation.Basic
        self.object_id = object_id

    def encode(self):
        ''' Encodes the request packet

        :returns: The byte encoded packet
        '''
        packet = struct.pack('>BBB', self.sub_function_code,
            self.read_code, self.object_id)
        return packet

    def decode(self, data):
        ''' Decodes data part of the message.

        :param data: The incoming data
        '''
        params = struct.unpack('>BBB', data)
        self.sub_function_code, self.read_code, self.object_id = params

    def execute(self, context):
        ''' Run a read exeception status request against the store

        :param context: The datastore to request from
        :returns: The populated response
        '''
        if not (0x00 <= self.object_id <= 0xff):
            return self.doException(merror.IllegalValue)
        if not (0x00 <= self.read_code <= 0x04):
            return self.doException(merror.IllegalValue)

        information = DeviceInformationFactory.get(_MCB,
            self.read_code, self.object_id)
        return ReadDeviceInformationResponse(self.read_code, information)

    def __str__(self):
        ''' Builds a representation of the request

        :returns: The string representation of the request
        '''
        params = (self.read_code, self.object_id)
        return "ReadDeviceInformationRequest(%d,%d)" % params


class ReadDeviceInformationResponse(ModbusResponse):
    '''
    '''
    function_code = 0x2b
    sub_function_code = 0x0e

    @classmethod
    def calculateRtuFrameSize(cls, buffer):
        ''' Calculates the size of the message

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the response.
        '''
        size  = 8 # skip the header information
        count = struct.unpack('>B', buffer[7])[0]

        while count > 0:
            _, object_length = struct.unpack('>BB', buffer[size:size+2])
            size += object_length + 2
            count -= 1
        return size + 2

    def __init__(self, read_code=None, information=None, **kwargs):
        ''' Initializes a new instance

        :param read_code: The device information read code
        :param information: The requested information request
        '''
        ModbusResponse.__init__(self, **kwargs)
        self.read_code = read_code or DeviceInformation.Basic
        self.information = information or {}
        self.number_of_objects = len(self.information)
        self.conformity = 0x83 # I support everything right now

        # TODO calculate
        self.next_object_id = 0x00 # self.information[-1](0)
        self.more_follows = MoreData.Nothing

    def encode(self):
        ''' Encodes the response

        :returns: The byte encoded message
        '''
        packet = struct.pack('>BBBBBB', self.sub_function_code,
            self.read_code, self.conformity, self.more_follows,
            self.next_object_id, self.number_of_objects)

        for (object_id, data) in self.information.items():
            packet += struct.pack('>BB', object_id, len(data))
            packet += data

        return packet

    def decode(self, data):
        ''' Decodes a the response

        :param data: The packet data to decode
        '''
        params = struct.unpack('>BBBBBB', data[0:6])
        self.sub_function_code, self.read_code = params[0:2]
        self.conformity, self.more_follows = params[2:4]
        self.next_object_id, self.number_of_objects = params[4:6]
        self.information, count = {}, 6 # skip the header information

        while count < len(data):
            object_id, object_length = struct.unpack('>BB', data[count:count+2])
            count += object_length + 2
            self.information[object_id] = data[count-object_length:count]

    def __str__(self):
        ''' Builds a representation of the response

        :returns: The string representation of the response
        '''
        return "ReadDeviceInformationResponse(%d)" % self.read_code

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "ReadDeviceInformationRequest", "ReadDeviceInformationResponse",
]
