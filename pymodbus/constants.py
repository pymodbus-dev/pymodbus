'''
Constants For Modbus Server/Client
----------------------------------

This is the single location for storing default
values for the servers and clients.
'''
from pymodbus.interfaces import Singleton

class Defaults(Singleton):
    ''' A collection of modbus default values
    '''
    Port = 502          # ''' The default modbus server port '''
    Retries = 3         # ''' The default client retries '''
    Timeout = 3000      # ''' The default client request timeout '''
    Reconnects = 0      # ''' The default number of reconnects '''
    TransactionId = 0   # ''' The default starting transaction identifier '''

#---------------------------------------------------------------------------# 
# Exported Identifiers
#---------------------------------------------------------------------------# 
__all__ = [ "Defaults" ]
