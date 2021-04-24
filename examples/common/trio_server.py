#!/usr/bin/env python
"""
Pymodbus Trio Server Example
--------------------------------------------------------------------------

"""
import logging

FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

import functools

from pymodbus.server.trio import tcp_server
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

import trio


async def run_server():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100),
    )

    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "Pymodbus"
    identity.ProductCode = "PM"
    identity.VendorUrl = "https://github.com/riptideio/pymodbus/"
    identity.ProductName = "Pymodbus Server"
    identity.ModelName = "Pymodbus Server"
    identity.MajorMinorRevision = "2.3.0"

    await trio.serve_tcp(
        functools.partial(
            tcp_server,
            context=context,
            identity=identity,
        ),
        port=5020,
        host="0.0.0.0",
    )


if __name__ == "__main__":
    trio.run(run_server)
