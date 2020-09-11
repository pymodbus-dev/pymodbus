'''
Constants For Modbus Server/Client
----------------------------------

This is the single location for storing default
values for the servers and clients.
'''
from pymodbus.interfaces import Singleton


class Defaults(Singleton):
    ''' A collection of modbus default values

    .. attribute:: Port

       The default modbus tcp server port (502)

    .. attribute:: TLSPort

       The default modbus tcp over tls server port (802)


    .. attribute:: Backoff

       The default exponential backoff delay (0.3 seconds)

    .. attribute:: Retries

       The default number of times a client should retry the given
       request before failing (3)

    .. attribute:: RetryOnEmpty

       A flag indicating if a transaction should be retried in the
       case that an empty response is received. This is useful for
       slow clients that may need more time to process a request.

    .. attribute:: RetryOnInvalid

       A flag indicating if a transaction should be retried in the
       case that an invalid response is received.

    .. attribute:: Timeout

       The default amount of time a client should wait for a request
       to be processed (3 seconds)

    .. attribute:: Reconnects

       The default number of times a client should attempt to reconnect
       before deciding the server is down (0)

    .. attribute:: TransactionId

       The starting transaction identifier number (0)

    .. attribute:: ProtocolId

       The modbus protocol id.  Currently this is set to 0 in all
       but proprietary implementations.

    .. attribute:: UnitId

       The modbus slave addrss.  Currently this is set to 0x00 which
       means this request should be broadcast to all the slave devices
       (really means that all the devices should respons).

    .. attribute:: Baudrate

       The speed at which the data is transmitted over the serial line.
       This defaults to 19200.

    .. attribute:: Parity

       The type of checksum to use to verify data integrity. This can be
       on of the following::

         - (E)ven - 1 0 1 0 | P(0)
         - (O)dd  - 1 0 1 0 | P(1)
         - (N)one - 1 0 1 0 | no parity

       This defaults to (N)one.

    .. attribute:: Bytesize

       The number of bits in a byte of serial data.  This can be one of
       5, 6, 7, or 8. This defaults to 8.

    .. attribute:: Stopbits

       The number of bits sent after each character in a message to
       indicate the end of the byte.  This defaults to 1.

    .. attribute:: ZeroMode

       Indicates if the slave datastore should use indexing at 0 or 1.
       More about this can be read in section 4.4 of the modbus specification.

    .. attribute:: IgnoreMissingSlaves

       In case a request is made to a missing slave, this defines if an error
       should be returned or simply ignored. This is useful for the case of a
       serial server emulater where a request to a non-existant slave on a bus
       will never respond. The client in this case will simply timeout.

    .. attribute:: broadcast_enable

      When False unit_id 0 will be treated as any other unit_id. When True and
      the unit_id is 0 the server will execute all requests on all server
      contexts and not respond and the client will skip trying to receive a
      response. Default value False does not conform to Modbus spec but maintains
      legacy behavior for existing pymodbus users.

    '''
    Port                = 502
    TLSPort             = 802
    Backoff             = 0.3
    Retries             = 3
    RetryOnEmpty        = False
    RetryOnInvalid      = False
    Timeout             = 3
    Reconnects          = 0
    TransactionId       = 0
    ProtocolId          = 0
    UnitId              = 0x00
    Baudrate            = 19200
    Parity              = 'N'
    Bytesize            = 8
    Stopbits            = 1
    ZeroMode            = False
    IgnoreMissingSlaves = False
    ReadSize            = 1024
    broadcast_enable    = False

class ModbusStatus(Singleton):
    '''
    These represent various status codes in the modbus
    protocol.

    .. attribute:: Waiting

       This indicates that a modbus device is currently
       waiting for a given request to finish some running task.

    .. attribute:: Ready

       This indicates that a modbus device is currently
       free to perform the next request task.

    .. attribute:: On

       This indicates that the given modbus entity is on

    .. attribute:: Off

       This indicates that the given modbus entity is off

    .. attribute:: SlaveOn

       This indicates that the given modbus slave is running

    .. attribute:: SlaveOff

       This indicates that the given modbus slave is not running
    '''
    Waiting  = 0xffff
    Ready    = 0x0000
    On       = 0xff00
    Off      = 0x0000
    SlaveOn  = 0xff
    SlaveOff = 0x00


class Endian(Singleton):
    ''' An enumeration representing the various byte endianess.

    .. attribute:: Auto

       This indicates that the byte order is chosen by the
       current native environment.

    .. attribute:: Big

       This indicates that the bytes are in little endian format

    .. attribute:: Little

       This indicates that the bytes are in big endian format

    .. note:: I am simply borrowing the format strings from the
       python struct module for my convenience.
    '''
    Auto   = '@'
    Big    = '>'
    Little = '<'


class ModbusPlusOperation(Singleton):
    ''' Represents the type of modbus plus request

    .. attribute:: GetStatistics

       Operation requesting that the current modbus plus statistics
       be returned in the response.

    .. attribute:: ClearStatistics

       Operation requesting that the current modbus plus statistics
       be cleared and not returned in the response.
    '''
    GetStatistics   = 0x0003
    ClearStatistics = 0x0004


class DeviceInformation(Singleton):
    ''' Represents what type of device information to read

    .. attribute:: Basic

       This is the basic (required) device information to be returned.
       This includes VendorName, ProductCode, and MajorMinorRevision
       code.

    .. attribute:: Regular

       In addition to basic data objects, the device provides additional
       and optinoal identification and description data objects. All of
       the objects of this category are defined in the standard but their
       implementation is optional.

    .. attribute:: Extended

       In addition to regular data objects, the device provides additional
       and optional identification and description private data about the
       physical device itself. All of these data are device dependent.

    .. attribute:: Specific

       Request to return a single data object.
    '''
    Basic    = 0x01
    Regular  = 0x02
    Extended = 0x03
    Specific = 0x04


class MoreData(Singleton):
    ''' Represents the more follows condition

    .. attribute:: Nothing

       This indiates that no more objects are going to be returned.

    .. attribute:: KeepReading

       This indicates that there are more objects to be returned.
    '''
    Nothing     = 0x00
    KeepReading = 0xFF

#---------------------------------------------------------------------------#
# Exported Identifiers
#---------------------------------------------------------------------------#
__all__ = [
    "Defaults", "ModbusStatus", "Endian",
    "ModbusPlusOperation",
    "DeviceInformation", "MoreData",
]
