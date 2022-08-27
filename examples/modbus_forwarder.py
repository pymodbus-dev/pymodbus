#!/usr/bin/env python3
"""Pymodbus synchronous forwarder.

This is a repeater or converter and  an example of just how powerful datastore is.

It consist of a server (any comm) and a client (any comm) and basically all request
received by the server is sent by client and all responses received by the
client is sent back by the server.

Both server and client are tcp based, but it can be easily modified to any server/client
(see client_sync.py and server_sync.py for other communication types)
"""
import argparse
import logging

from pymodbus.client import ModbusTcpClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.server.sync import StartTcpServer


def run_forwarder():
    """Run forwarder setup."""
    port_server, port_client, slaves = get_commandline()

    client = ModbusTcpClient(
        host="localhost",
        port=port_client,
    )

    # If required to communicate with a specified client use unit=<unit_id>
    # in RemoteSlaveContext
    # For e.g to forward the requests to slave with unit address 1 use
    # store = RemoteSlaveContext(client, unit=1)
    if slaves:
        store = {}
        for i in slaves:
            store[i.to_bytes(1, "big")] = RemoteSlaveContext(client, unit=i)
    else:
        store = RemoteSlaveContext(client)
    context = ModbusServerContext(slaves=store, single=True)

    # start forwarding client and server
    client.connect()
    StartTcpServer(context, address=("localhost", port_server))
    # loop forever


# --------------------------------------------------------------------------- #
# Extra code, to allow commandline parameters instead of changing the code
# --------------------------------------------------------------------------- #
FORMAT = "%(asctime)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
logging.basicConfig(format=FORMAT)
_logger = logging.getLogger()


def get_commandline():
    """Read and validate command line arguments"""
    parser = argparse.ArgumentParser(description="Command line options for examples")
    parser.add_argument(
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help='"critical", "error", "warning", "info" or "debug"',
        type=str,
    )
    parser.add_argument(
        "--port",
        help="the port to use",
        type=int,
    )
    parser.add_argument(
        "--port_client",
        help="the port to use",
        type=int,
    )
    parser.add_argument(
        "--slaves",
        help="list of slaves to forward",
        type=int,
        nargs="+",
    )
    args = parser.parse_args()

    # set defaults
    _logger.setLevel(args.log.upper() if args.log else logging.INFO)
    if not args.port:
        args.port = 5020
    if not args.port_client:
        args.port_client = 5010

    return args.port, args.port_client, args.slaves


if __name__ == "__main__":
    run_forwarder()
