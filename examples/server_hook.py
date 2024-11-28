#!/usr/bin/env python3
"""Pymodbus Server With request/response manipulator.

This is an example of using the builtin request/response tracer to
manipulate the messages to/from the modbus server
"""
from __future__ import annotations

import asyncio
import logging

from pymodbus import FramerType, pymodbus_apply_logging_config
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.pdu import ModbusPDU
from pymodbus.server import ModbusTcpServer


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
        print(f"---> {"REQUEST pdu" if sending else "RESPONSE pdu"}: {pdu}")
        return pdu

    def trace_connect(self, connect: bool) -> None:
        """Do dummy trace."""
        print(f"---> {"Connected" if connect else "Disconnected"}")

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
            framer=FramerType.SOCKET,
            identity=None,
            address=("127.0.0.1", 5020),
            trace_packet=self.trace_packet,
            trace_pdu=self.trace_pdu,
            trace_connect=self.trace_connect,
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
