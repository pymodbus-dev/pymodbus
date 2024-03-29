#!/usr/bin/env python3
"""Pymodbus Server With request/response manipulator.

This is an example of using the builtin request/response tracer to
manipulate the messages to/from the modbus server
"""
import asyncio
import logging

from pymodbus import FramerType, pymodbus_apply_logging_config
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.server import ModbusTcpServer


class Manipulator:
    """A Class to run the server.

    Using a class allows the easy use of global variables, but
    are not strictly needed
    """

    message_count: int = 1
    server: ModbusTcpServer = None

    def server_request_tracer(self, request, *_addr):
        """Trace requests.

        All server requests passes this filter before being handled.
        """
        print(f"---> REQUEST: {request}")

    def server_response_manipulator(self, response):
        """Manipulate responses.

        All server responses passes this filter before being sent.
        The filter returns:

        - response, either original or modified
        - skip_encoding, signals whether or not to encode the response
        """
        if not self.message_count:
            print(f"---> RESPONSE: {response}")
            self.message_count = 3
        else:
            print("---> RESPONSE: NONE")
            response.should_respond = False
            self.message_count -= 1
        return response, False

    async def setup(self):
        """Prepare server."""
        pymodbus_apply_logging_config(logging.DEBUG)
        datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
        context = ModbusServerContext(
            slaves=ModbusSlaveContext(
                di=datablock, co=datablock, hr=datablock, ir=datablock
            ),
            single=True,
        )
        self.server = ModbusTcpServer(
            context,
            FramerType.SOCKET,
            None,
            ("127.0.0.1", 5020),
            request_tracer=self.server_request_tracer,
            response_manipulator=self.server_response_manipulator,
        )

    async def run(self):
        """Attach Run server."""
        await self.server.serve_forever()


async def main():
    """Run example."""
    server = Manipulator()
    await server.setup()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
