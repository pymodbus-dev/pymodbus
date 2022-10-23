#!/usr/bin/env python3
# pylint: disable=missing-any-param-doc,differing-param-doc
"""Pymodbus Server With Updating Thread.

This is an example of having a background thread updating the
context while the server is operating. This can also be done with
a python thread::

    from threading import Thread
    Thread(target=updating_writer, args=(context,)).start()
"""
import asyncio
import logging

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartAsyncTcpServer
from pymodbus.version import version


# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(extra):
    """Run every so often,

    and updates live values of the context. It should be noted
    that there is a lrace condition for the update.

    :param arguments: The input arguments to the call
    """
    log.debug("updating the context")
    context = extra[0]
    register = 3
    slave_id = 0x00
    address = 0x10
    values = context[slave_id].getValues(register, address, count=5)
    values = [v + 1 for v in values]
    txt = f"new values: {str(values)}"
    log.debug(txt)
    context[slave_id].setValues(register, address, values)


async def run_updating_server():
    """Run updating server."""
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100),
    )
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/riptideio/pymodbus/",
            "ProductName": "pymodbus Server",
            "ModelName": "pymodbus Server",
            "MajorMinorRevision": version.short(),
        }
    )

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    log.debug("Start server")
    await StartAsyncTcpServer(
        context, identity=identity, address=("localhost", 5020), defer_start=False
    )
    log.debug("Done")


if __name__ == "__main__":
    asyncio.run(run_updating_server())
