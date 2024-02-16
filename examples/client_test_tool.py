#!/usr/bin/env python3
"""Pymodbus client testing tool.

usage::

    client_test_tool.py

This is a tool to test how a client react to responses from a malicious server.

The tool is intended for users with advanced modbus protocol knowledge.

When testing a client the server is replaced by a stub and the nullmodem solution.

There are 2 functions which can be modified to test the client functionality.

*** client_calls(client) ***

    Called when the client is connected.

    The full client API is available, just as if it was a normal App using pymodbus

*** handle_stub_data(transport, data) ***

    Called when the client sends data (remark data is frame+request)

    The function generates frame+response and sends it.
"""
from __future__ import annotations

import asyncio
from typing import Callable

import pymodbus.client as modbusClient
from pymodbus import pymodbus_apply_logging_config
from pymodbus.logging import Log
from pymodbus.transport import NULLMODEM_HOST, CommParams, CommType, ModbusProtocol


class ServerStub(ModbusProtocol):
    """Protocol layer including transport."""

    def __init__(
        self,
        params: CommParams,
        is_server: bool,
        handler: Callable[[bytes], bytes],
    ) -> None:
        """Initialize a stub instance."""
        self.stub_handle_data = handler
        super().__init__(params, is_server)

    async def start_run(self):
        """Call need functions to start server/client."""
        if  self.is_server:
            return await self.transport_listen()
        return await self.transport_connect()

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        self.stub_handle_data(self, data)
        return len(data)

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        new_stub = ServerStub(self.comm_params, False, self.stub_handle_data)
        new_stub.stub_handle_data = self.stub_handle_data
        return new_stub


class ClientTester:  # pylint: disable=too-few-public-methods
    """Main program."""

    def __init__(self, comm: CommType):
        """Initialize runtime tester."""
        self.comm = comm

        if comm == CommType.TCP:
            self.client = modbusClient.AsyncModbusTcpClient(
                        NULLMODEM_HOST,
                        port=5004,
            )
        elif comm == CommType.SERIAL:
            self.client = modbusClient.AsyncModbusSerialClient(
                        f"{NULLMODEM_HOST}:5004",
            )
        else:
            raise RuntimeError("ERROR: CommType not implemented")
        server_params = self.client.comm_params.copy()
        server_params.source_address = (f"{NULLMODEM_HOST}:5004", 5004)
        self.stub = ServerStub(server_params, True, handle_stub_data)


    async def run(self):
        """Execute test run."""
        pymodbus_apply_logging_config()
        Log.debug("--> Start testing.")
        await self.stub.start_run()
        await self.client.connect()
        assert self.client.connected
        await client_calls(self.client)
        Log.debug("--> Closing.")
        self.client.close()


async def main(comm: CommType):
    """Combine setup and run."""
    test = ClientTester(comm)
    await test.run()


# -------------- USER CHANGES --------------

async def client_calls(client):
    """Test client API."""
    Log.debug("--> Client calls starting.")
    _resp = await client.read_holding_registers(address=124, count=4, slave=1)

def handle_stub_data(transport: ModbusProtocol, data: bytes):
    """Respond to request at transport level."""
    Log.debug("--> stub called with request {}.", data, ":hex")
    response = b'\x01\x03\x08\x00\x05\x00\x05\x00\x00\x00\x00\x0c\xd7'
    transport.transport_send(response)


if __name__ == "__main__":
    asyncio.run(main(CommType.SERIAL), debug=True)
