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
    '''
    Port          = 502
    Retries       = 3
    Timeout       = 3000
    Reconnects    = 0
    TransactionId = 0
    ProtocolId    = 0

#---------------------------------------------------------------------------# 
# Exported Identifiers
#---------------------------------------------------------------------------# 
__all__ = [ "Defaults" ]
