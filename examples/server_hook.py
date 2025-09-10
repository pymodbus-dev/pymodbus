#!/usr/bin/env python3
"""Pymodbus Server With request/response manipulator.

This is an example of using the builtin request/response tracer to
manipulate the messages to/from the modbus server
"""
from __future__ import annotations

import asyncio
import logging
import sys

from pymodbus import FramerType, pymodbus_apply_logging_config
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.pdu import ModbusPDU
from pymodbus.server import ModbusTcpServer


try:
    import helper  # type: ignore[import-not-found]
except ImportError:
    print("*** ERROR --> THIS EXAMPLE needs the example directory, please see \n\
          https://pymodbus.readthedocs.io/en/latest/source/examples.html\n\
          for more information.")
    sys.exit(-1)


class Manipulator:
    """A Class to run the server."""

    message_count: int = 1
    server: ModbusTcpServer

    def trace_packet(self, sending: bool, data: bytes) -> bytes:
        """Do dummy trace."""
        txt = "REQUEST stream" if sending else "RESPONSE stream"
        print(f"---> {txt}: {data!r}")

        return data

    def trace_pdu(self, sending: bool, pdu: ModbusPDU) -> ModbusPDU:
        """Do dummy trace."""
        txt = "REQUEST pdu" if sending else "RESPONSE pdu"
        print(f"---> {txt}: {pdu}")
        return pdu

    def trace_connect(self, connect: bool) -> None:
        """Do dummy trace."""
        txt = "Connected" if connect else "Disconnected"
        print(f"---> {txt}")

    async def setup(self, cmdline):
        """Prepare server."""
        args = helper.get_commandline(server=True, description="server hooks", cmdline=cmdline)
        pymodbus_apply_logging_config(logging.DEBUG)
        datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
        context = ModbusServerContext(
            devices=ModbusDeviceContext(
                di=datablock, co=datablock, hr=datablock, ir=datablock
            ),
            single=True,
        )
        address: tuple[str, int] = (args.host if args.host else "", args.port if args.port else 0)
        self.server = ModbusTcpServer(
            context,
            framer=FramerType.SOCKET,
            identity=None,
            address=address,
            trace_packet=self.trace_packet,
            trace_pdu=self.trace_pdu,
            trace_connect=self.trace_connect,
        )

    async def run(self):
        """Attach Run server."""
        await self.server.serve_forever()


async def main(cmdline=None):
    """Run example."""
    server = Manipulator()
    await server.setup(cmdline=cmdline)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
