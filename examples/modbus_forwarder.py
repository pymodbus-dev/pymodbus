#!/usr/bin/env python3
"""Pymodbus synchronous forwarder.

This is a repeater or converter and  an example of just how powerful datastore is.

It consist of a server (any comm) and a client (any comm) and basically all request
received by the server is sent by client and all responses received by the
client is sent back by the server.

Both server and client are tcp based, but it can be easily modified to any server/client
(see client_sync.py and server_sync.py for other communication types)
"""
import asyncio
import logging

from examples.helper import get_commandline
from pymodbus.client import ModbusTcpClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.server import StartAsyncTcpServer


_logger = logging.getLogger()


def setup_forwarder(args):
    """Do setup forwarder."""
    args.client = ModbusTcpClient(
        host="localhost",
        port=args.client_port,
    )

    # If required to communicate with a specified client use unit=<unit_id>
    # in RemoteSlaveContext
    # For e.g to forward the requests to slave with unit address 1 use
    # store = RemoteSlaveContext(client, unit=1)
    if args.slaves:
        store = {}
        for i in args.slaves:
            store[i.to_bytes(1, "big")] = RemoteSlaveContext(args.client, unit=i)
    else:
        store = RemoteSlaveContext(args.client)
    args.context = ModbusServerContext(slaves=store, single=True)
    return args


async def run_forwarder(args):
    """Run forwarder setup."""
    txt = f"### start forwarder, listen {args.port}, connect to {args.client_port}"
    _logger.info(txt)

    # start forwarding client and server
    args.client.connect()
    await StartAsyncTcpServer(context=args.context, address=("localhost", args.port))
    # loop forever


if __name__ == "__main__":
    cmd_args = get_commandline(
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
    run_args = setup_forwarder(cmd_args)
    asyncio.run(run_forwarder(run_args))
