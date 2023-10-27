#!/usr/bin/env python3
"""Pymodbus Server With Callbacks.

This is an example of adding callbacks to a running modbus server
when a value is written to it.
"""
import asyncio
import logging

import server_async

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class CallbackDataBlock(ModbusSequentialDataBlock):
    """A datablock that stores the new value in memory,.

    and passes the operation to a message queue for further processing.
    """

    def __init__(self, queue, addr, values):
        """Initialize."""
        self.queue = queue
        super().__init__(addr, values)

    def setValues(self, address, value):
        """Set the requested values of the datastore."""
        super().setValues(address, value)
        txt = f"Callback from setValues with address {address}, value {value}"
        _logger.debug(txt)

    def getValues(self, address, count=1):
        """Return the requested values from the datastore."""
        result = super().getValues(address, count=count)
        txt = f"Callback from getValues with address {address}, count {count}, data {result}"
        _logger.debug(txt)
        return result

    def validate(self, address, count=1):
        """Check to see if the request is in range."""
        result = super().validate(address, count=count)
        txt = f"Callback from validate with address {address}, count {count}, data {result}"
        _logger.debug(txt)
        return result


async def run_callback_server(cmdline=None):
    """Define datastore callback for server and do setup."""
    queue = asyncio.Queue()
    block = CallbackDataBlock(queue, 0x00, [17] * 100)
    block.setValues(1, 15)
    store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    context = ModbusServerContext(slaves=store, single=True)
    run_args = server_async.setup_server(
        description="Run callback server.", cmdline=cmdline, context=context
    )
    await server_async.run_async_server(run_args)


if __name__ == "__main__":
    asyncio.run(run_callback_server(), debug=True)  # pragma: no cover
