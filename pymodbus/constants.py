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

    .. attribute:: Retries

       The default number of times a client should retry the given
       request before failing (3)

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
    '''
    Port          = 502
    Retries       = 3
    Timeout       = 3
    Reconnects    = 0
    TransactionId = 0
    ProtocolId    = 0
    UnitId        = 0x00
    Baudrate      = 19200
    Parity        = 'N'
    Bytesize      = 8
    Stopbits      = 1

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

#---------------------------------------------------------------------------# 
# Exported Identifiers
#---------------------------------------------------------------------------# 
__all__ = [ "Defaults", "ModbusStatus" ]
