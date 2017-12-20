#!/usr/bin/env python
"""
Pymodbus Server With Custom Datablock Side Effect
--------------------------------------------------------------------------

This is an example of performing custom logic after a value has been
written to the datastore.
"""
# --------------------------------------------------------------------------- # 
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from __future__ import print_function
from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

# --------------------------------------------------------------------------- # 
# configure the service logging
# --------------------------------------------------------------------------- # 

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- # 
# create your custom data block here
# --------------------------------------------------------------------------- # 


class CustomDataBlock(ModbusSparseDataBlock):
    """ A datablock that stores the new value in memory
    and performs a custom action after it has been stored.
    """

    def setValues(self, address, value):
        """ Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        """
        super(ModbusSparseDataBlock, self).setValues(address, value)

        # whatever you want to do with the written value is done here,
        # however make sure not to do too much work here or it will
        # block the server, espectially if the server is being written
        # to very quickly
        print("wrote {} to {}".format(value, address))


def run_custom_db_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    block  = CustomDataBlock([0]*100)
    store  = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #

    identity = ModbusDeviceIdentification()
    identity.VendorName = 'pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'pymodbus Server'
    identity.ModelName = 'pymodbus Server'
    identity.MajorMinorRevision = '1.0'

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #

    # p = Process(target=device_writer, args=(queue,))
    # p.start()
    StartTcpServer(context, identity=identity, address=("localhost", 5020))


if __name__ == "__main__":
    run_custom_db_server()


