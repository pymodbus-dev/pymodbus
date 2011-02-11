from pymodbus.exceptions import NotImplementedException, ParameterException
from pymodbus.interfaces import IModbusSlaveContext

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging;
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Context
#---------------------------------------------------------------------------#
class RemoteSlaveContext(IModbusSlaveContext):
    ''' TODO
    This creates a modbus data model that connects to
    a remote device (depending on the client used)
    '''

    def __init__(self, client):
        ''' Initializes the datastores

        :param client: The client to retrieve values with
        '''
        self.client = client

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        raise NotImplementedException("Context Reset")

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        raise NotImplementedException("Context Reset")

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Remote Slave Context(%s)" % self.client

