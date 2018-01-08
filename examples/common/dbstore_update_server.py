"""
Pymodbus Server With Updating Thread
--------------------------------------------------------------------------
This is an example of having a background thread updating the
context in an SQLite4 database while the server is operating.

This scrit generates a random address range (within 0 - 65000) and a random
value and stores it in a database. It then reads the same address to verify
that the process works as expected

This can also be done with a python thread::
    from threading import Thread
    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
"""
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.database import SqlSlaveContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
import random

# --------------------------------------------------------------------------- #
# import the twisted libraries we need
# --------------------------------------------------------------------------- #
from twisted.internet.task import LoopingCall

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    """ A worker process that runs every so often and
    updates live values of the context which resides in an SQLite3 database.
    It should be noted that there is a race condition for the update.
    :param arguments: The input arguments to the call
    """
    log.debug("Updating the database context")
    context  = a[0]
    readfunction = 0x03 # read holding registers
    writefunction = 0x10
    slave_id = 0x01 # slave address
    count = 50

    # import pdb; pdb.set_trace()

    rand_value = random.randint(0, 9999)
    rand_addr = random.randint(0, 65000)
    log.debug("Writing to datastore: {}, {}".format(rand_addr, rand_value))
    # import pdb; pdb.set_trace()
    context[slave_id].setValues(writefunction, rand_addr, [rand_value])
    values = context[slave_id].getValues(readfunction, rand_addr, count)
    log.debug("Values from datastore: " + str(values))


def run_dbstore_update_server():
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #

    block = ModbusSequentialDataBlock(0x00, [0] * 0xff)
    store = SqlSlaveContext(block)

    context = ModbusServerContext(slaves={1: store}, single=False)

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
    time = 5  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,))
    loop.start(time, now=False)  # initially delay by time
    StartTcpServer(context, identity=identity, address=("", 5020))


if __name__ == "__main__":
    run_dbstore_update_server()


