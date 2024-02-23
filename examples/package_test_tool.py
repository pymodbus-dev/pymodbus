#!/usr/bin/env python3
"""Pymodbus client testing tool.

usage::

    package_test_tool.py

This is a tool to test how a client react to responses from a malicious server using:

    ClientTester

and to how the server react to requests using:

    ServerTester

The tool is intended for users with advanced modbus protocol knowledge.

When testing a client the server is replaced by a stub and the nullmodem solution.

There are 4 functions which can be modified to test the client/server functionality.

*** client_calls(client) ***

    Called when the client is connected.

    The full client API is available, just as if it was a normal App using pymodbus

*** server_calls(transport) ***

    Called when the server is listening and stub connected.

    Send raw data packets to the server (remark data is frame+request)

*** handle_client_data(transport, data) ***

    Called when data is received from the client/server (remark data is frame+request)

    The function generates frame+response and sends it.

And one function which can be modified to test the server functionality:
"""
from __future__ import annotations

import asyncio
from typing import Callable

import pymodbus.client as modbusClient
import pymodbus.server as modbusServer
from pymodbus import Framer, pymodbus_apply_logging_config
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.logging import Log
from pymodbus.transport import NULLMODEM_HOST, CommParams, CommType, ModbusProtocol


class TransportStub(ModbusProtocol):
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
            return await self.listen()
        return await self.connect()

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        self.stub_handle_data(self, data)
        return len(data)

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        new_stub = TransportStub(self.comm_params, False, self.stub_handle_data)
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
        self.stub = TransportStub(server_params, True, handle_client_data)


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


class ServerTester:  # pylint: disable=too-few-public-methods
    """Main program."""

    def __init__(self, comm: CommType):
        """Initialize runtime tester."""
        self.comm = comm
        self.store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)
        self.identity = ModbusDeviceIdentification(
            info_name={"VendorName": "VendorName"}
        )
        if comm == CommType.TCP:
            self.server = modbusServer.ModbusTcpServer(
                self.context,
                framer=Framer.SOCKET,
                identity=self.identity,
                address=(NULLMODEM_HOST, 5004),
            )
        elif comm == CommType.SERIAL:
            self.server = modbusServer.ModbusSerialServer(
                self.context,
                framer=Framer.SOCKET,
                identity=self.identity,
                port=f"{NULLMODEM_HOST}:5004",
            )
        else:
            raise RuntimeError("ERROR: CommType not implemented")
        client_params = self.server.comm_params.copy()
        client_params.host = client_params.source_address[0]
        client_params.port = client_params.source_address[1]
        client_params.timeout_connect = 1.0
        self.stub = TransportStub(client_params, False, handle_server_data)


    async def run(self):
        """Execute test run."""
        pymodbus_apply_logging_config()
        Log.debug("--> Start testing.")
        await self.server.listen()
        await self.stub.start_run()
        await server_calls(self.stub)
        Log.debug("--> Shutting down.")
        await self.server.shutdown()


async def main(comm: CommType, use_server: bool):
    """Combine setup and run."""
    if use_server:
        test = ServerTester(comm)
    else:
        test = ClientTester(comm)
    await test.run()


# -------------- USER CHANGES --------------

async def client_calls(client):
    """Test client API."""
    Log.debug("--> Client calls starting.")
    _resp = await client.read_holding_registers(address=124, count=4, slave=0)


async def server_calls(transport: ModbusProtocol):
    """Test client API."""
    Log.debug("--> Server calls starting.")
    _resp = transport.send(b'\x00\x02\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01' +
        b'\x07\x00\x03\x00\x00\x06\x01\x03\x00\x00\x00\x01')
    await asyncio.sleep(1)
    print("---> all done")

def handle_client_data(transport: ModbusProtocol, data: bytes):
    """Respond to request at transport level."""
    Log.debug("--> stub called with request {}.", data, ":hex")
    response = b'\x01\x03\x08\x00\x05\x00\x05\x00\x00\x00\x00\x0c\xd7'

    # Multiple send is allowed, to test fragmentation
    #  for data in response:
    #    to_send = data.to_bytes()
    #    transport.send(to_send)
    transport.send(response)


def handle_server_data(_transport: ModbusProtocol, data: bytes):
    """Respond to request at transport level."""
    Log.debug("--> stub called with response {}.", data, ":hex")


if __name__ == "__main__":
    # True for Server test, False for Client test
    # asyncio.run(main(CommType.SERIAL, False), debug=True)
    asyncio.run(main(CommType.TCP, True), debug=True)
