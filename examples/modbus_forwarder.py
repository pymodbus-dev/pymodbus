#!/usr/bin/env python3
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
from __future__ import annotations

import asyncio
import logging
import sys


try:
    import helper  # type: ignore[import-not-found]
except ImportError:
    print("*** ERROR --> THIS EXAMPLE needs the example directory, please see \n\
          https://pymodbus.readthedocs.io/en/latest/source/examples.html\n\
          for more information.")
    sys.exit(-1)

from pymodbus.client import ModbusTcpClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteDeviceContext
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
    # If required to communicate with a specified client use device_id=<device id>
    # in RemoteDeviceContext
    # For e.g to forward the requests to device_id with device address 1 use
    # store = RemoteDeviceContext(client, device_id=1)
    store: dict | RemoteDeviceContext
    if args.device_ids:
        store = {}
        for i in args.device_ids:
            store[i.to_bytes(1, "big")] = RemoteDeviceContext(args.client, device_id=i)
    else:
        store = RemoteDeviceContext(args.client, device_id=1)
    args.context = ModbusServerContext(devices=store, single=True)

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
    asyncio.run(async_helper())
