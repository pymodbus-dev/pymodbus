#!/usr/bin/env python3
""" Pymodbus Server With Custom Datablock Side Effect
--------------------------------------------------------------------------

This is an example of performing custom logic after a value has been
written to the datastore.
"""
from __future__ import print_function
import logging

# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.version import version
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# create your custom data block here
# --------------------------------------------------------------------------- #


class CustomDataBlock(ModbusSparseDataBlock):
    """ A datablock that stores the new value in memory
    and performs a custom action after it has been stored.
    """

    def setValues(self, address, value): # pylint: disable=arguments-differ
        """ Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        """
        super().setValues(address, value)

        # whatever you want to do with the written value is done here,
        # however make sure not to do too much work here or it will
        # block the server, espectially if the server is being written
        # to very quickly
        print(f"wrote {value} to {address}")


def run_custom_db_server():
    """ Run custom db server. """
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    block = CustomDataBlock([0] * 100)
    store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #

    identity = ModbusDeviceIdentification(info_name= {
        'VendorName': 'pymodbus',
        'ProductCode': 'PM',
        'VendorUrl': 'http://github.com/riptideio/pymodbus/', #NOSONAR
        'ProductName': 'pymodbus Server',
        'ModelName': 'pymodbus Server',
        'MajorMinorRevision': version.short(),
    })

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #

    # p = Process(target=device_writer, args=(queue,))
    # p.start()
    StartTcpServer(context, identity=identity, address=("localhost", 5020))


if __name__ == "__main__":
    run_custom_db_server()
