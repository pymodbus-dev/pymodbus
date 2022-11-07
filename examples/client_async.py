#!/usr/bin/env python3
"""Pymodbus Aynchronous Client Example.

An example of a single threaded synchronous client.

usage: client_async.py [-h] [--comm {tcp,udp,serial,tls}]
                       [--framer {ascii,binary,rtu,socket,tls}]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT]
options:
  -h, --help            show this help message and exit
  --comm {tcp,udp,serial,tls}
                        "serial", "tcp", "udp" or "tls"
  --framer {ascii,binary,rtu,socket,tls}
                        "ascii", "binary", "rtu", "socket" or "tls"
  --log {critical,error,warning,info,debug}
                        "critical", "error", "warning", "info" or "debug"
  --port PORT           the port to use

The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
import asyncio
import logging
import os

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from examples.helper import get_commandline
from pymodbus.client import (
    AsyncModbusSerialClient,
    AsyncModbusTcpClient,
    AsyncModbusTlsClient,
    AsyncModbusUdpClient,
)


_logger = logging.getLogger()


def setup_async_client(args):
    """Run client setup."""
    _logger.info("### Create client object")
    if args.comm == "tcp":
        client = AsyncModbusTcpClient(
            args.host,
            port=args.port,  # on which port
            # Common optional paramers:
            framer=args.framer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # TCP setup parameters
            #    source_address=("localhost", 0),
        )
    elif args.comm == "udp":
        client = AsyncModbusUdpClient(
            args.host,
            port=args.port,
            # Common optional paramers:
            framer=args.framer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # UDP setup parameters
            #    source_address=None,
        )
    elif args.comm == "serial":
        client = AsyncModbusSerialClient(
            args.port,
            # Common optional paramers:
            #    framer=ModbusRtuFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # Serial setup parameters
            #    baudrate=9600,
            #    bytesize=8,
            #    parity="N",
            #    stopbits=1,
            #    handle_local_echo=False,
        )
    elif args.comm == "tls":
        cwd = os.getcwd().split("/")[-1]
        if cwd == "examples":
            path = "."
        elif cwd == "test":
            path = "../examples"
        else:
            path = "examples"
        client = AsyncModbusTlsClient(
            args.host,
            port=args.port,
            # Common optional paramers:
            framer=args.framer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # TLS setup parameters
            #    sslctx=sslctx,
            certfile=f"{path}/certificates/pymodbus.crt",
            keyfile=f"{path}/certificates/pymodbus.key",
            #    password="none",
            server_hostname="localhost",
        )
    return client


async def run_async_client(client, modbus_calls=None):
    """Run sync client."""
    _logger.info("### Client starting")
    await client.connect()
    assert client.protocol
    if modbus_calls:
        await modbus_calls(client)
    await client.close()
    _logger.info("### End of Program")


if __name__ == "__main__":
    cmd_args = get_commandline(
        server=False,
        description="Run asynchronous client.",
    )
    testclient = setup_async_client(cmd_args)
    asyncio.run(run_async_client(testclient), debug=True)
