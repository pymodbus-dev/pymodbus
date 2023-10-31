#!/usr/bin/env python3
# pragma no cover
"""Pymodbus synchronous forwarder.

This is a repeater or converter and an example of just how powerful datastore is.

It consist of a server (any comm) and a client (any comm), functionality:

a) server receives a read/write request from external client:

    - client sends a new read/write request to target server
    - client receives response and updates the datastore
    - server sends new response to external client

Both server and client are tcp based, but it can be easily modified to any server/client
(see client_sync.py and server_sync.py for other communication types)

**WARNING** This example is a simple solution, that do only forward read requests.
"""
import asyncio
import logging

import helper

from pymodbus.client import ModbusTcpClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.server import StartAsyncTcpServer


_logger = logging.getLogger(__file__)


async def setup_forwarder(args):
    """Do setup forwarder."""
    return args


async def run_forwarder(args):
    """Run forwarder setup."""
    txt = f"### start forwarder, listen {args.port}, connect to {args.client_port}"
    _logger.info(txt)

    args.client = ModbusTcpClient(
        host="localhost",
        port=args.client_port,
    )
    args.client.connect()
    assert args.client.connected
    # If required to communicate with a specified client use slave=<slave_id>
    # in RemoteSlaveContext
    # For e.g to forward the requests to slave with slave address 1 use
    # store = RemoteSlaveContext(client, slave=1)
    if args.slaves:
        store = {}
        for i in args.slaves:
            store[i.to_bytes(1, "big")] = RemoteSlaveContext(args.client, slave=i)
    else:
        store = RemoteSlaveContext(args.client, slave=1)
    args.context = ModbusServerContext(slaves=store, single=True)

    await StartAsyncTcpServer(context=args.context, address=("", args.port))
    # loop forever


async def async_helper():
    """Combine setup and run."""
    cmd_args = helper.get_commandline(
        server=True,
        description="Run asynchronous forwarder.",
        extras=[
            (
                "--client_port",
                {
                    "help": "the port to use",
                    "type": int,
                },
            )
        ],
    )
    await run_forwarder(cmd_args)


if __name__ == "__main__":
    asyncio.run(async_helper())  # pragma: no cover
