#!/usr/bin/env python3
"""Pymodbus asynchronous Server Example.

An example of a multi threaded asynchronous server.

usage: server_async.py [-h] [--comm {tcp,udp,serial,tls}]
                       [--framer {ascii,binary,rtu,socket,tls}]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT] [--store {sequential,sparse,factory,none}]
                       [--slaves SLAVES]

Command line options for examples

options:
  -h, --help            show this help message and exit
  --comm {tcp,udp,serial,tls}
                        "serial", "tcp", "udp" or "tls"
  --framer {ascii,binary,rtu,socket,tls}
                        "ascii", "binary", "rtu", "socket" or "tls"
  --log {critical,error,warning,info,debug}
                        "critical", "error", "warning", "info" or "debug"
  --port PORT           the port to use
  --store {sequential,sparse,factory,none}
                        "sequential", "sparse", "factory" or "none"
  --slaves SLAVES       number of slaves to respond to

The corresponding client can be started as:
    python3 client_sync.py
"""
import asyncio
import logging
import os

from examples.helper import get_commandline
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.server import (
    StartAsyncSerialServer,
    StartAsyncTcpServer,
    StartAsyncTlsServer,
    StartAsyncUdpServer,
)
from pymodbus.version import version


_logger = logging.getLogger()


def setup_server(args):
    """Run server setup."""
    # The datastores only respond to the addresses that are initialized
    # If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
    # 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)
    if not args.context:
        _logger.info("### Create datastore")
        if args.store == "sequential":
            # Continuing, use a sequential block without gaps.
            datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
        elif args.store == "sparse":
            # Continuing, or use a sparse DataBlock which can have gaps
            datablock = ModbusSparseDataBlock({0x00: 0, 0x05: 1})
        elif args.store == "factory":
            # Alternately, use the factory methods to initialize the DataBlocks
            # or simply do not pass them to have them initialized to 0x00 on the
            # full address range::
            datablock = ModbusSequentialDataBlock.create()

        if args.slaves:
            # The server then makes use of a server context that allows the server
            # to respond with different slave contexts for different unit ids.
            # By default it will return the same context for every unit id supplied
            # (broadcast mode).
            # However, this can be overloaded by setting the single flag to False and
            # then supplying a dictionary of unit id to context mapping::
            #
            # The slave context can also be initialized in zero_mode which means
            # that a request to address(0-7) will map to the address (0-7).
            # The default is False which is based on section 4.4 of the
            # specification, so address(0-7) will map to (1-8)::
            context = {
                0x01: ModbusSlaveContext(
                    di=datablock,
                    co=datablock,
                    hr=datablock,
                    ir=datablock,
                ),
                0x02: ModbusSlaveContext(
                    di=datablock,
                    co=datablock,
                    hr=datablock,
                    ir=datablock,
                ),
                0x03: ModbusSlaveContext(
                    di=datablock,
                    co=datablock,
                    hr=datablock,
                    ir=datablock,
                    zero_mode=True,
                ),
            }
            single = False
        else:
            context = ModbusSlaveContext(
                di=datablock, co=datablock, hr=datablock, ir=datablock, unit=1
            )
            single = True

        # Build data storage
        args.context = ModbusServerContext(slaves=context, single=single)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    args.identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": version.short(),
        }
    )
    return args


async def run_async_server(args):
    """Run server."""
    txt = f"### start ASYNC server, listening on {args.port} - {args.comm}"
    _logger.info(txt)
    if args.comm == "tcp":
        address = ("", args.port) if args.port else None
        server = await StartAsyncTcpServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            # TBD host=
            # TBD port=
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # handler=None,  # handler for each session
            allow_reuse_address=True,  # allow the reuse of an address
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
            # defer_start=False,  # Only define server do not activate
        )
    elif args.comm == "udp":
        address = ("127.0.0.1", args.port) if args.port else None
        server = await StartAsyncUdpServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # handler=None,  # handler for each session
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
            # defer_start=False,  # Only define server do not activate
        )
    elif args.comm == "serial":
        # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600
        #             PTY,link=/tmp/ttyp0,raw,echo=0,ospeed=9600
        server = await StartAsyncSerialServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            # timeout=1,  # waiting time for request to complete
            port=args.port,  # serial port
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # handler=None,  # handler for each session
            # stopbits=1,  # The number of stop bits to use
            # bytesize=8,  # The bytesize of the serial messages
            # parity="N",  # Which kind of parity to use
            # baudrate=9600,  # The baud rate to use for the serial device
            # handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # strict=True,  # use strict timing, t1.5 for Modbus RTU
            # defer_start=False,  # Only define server do not activate
        )
    elif args.comm == "tls":
        address = ("", args.port) if args.port else None
        cwd = os.getcwd().split("/")[-1]
        if cwd == "examples":
            path = "."
        elif cwd == "test":
            path = "../examples"
        else:
            path = "examples"
        server = await StartAsyncTlsServer(
            context=args.context,  # Data storage
            host="localhost",  # define tcp address where to connect to.
            # port=port,  # on which port
            identity=args.identity,  # server identify
            # custom_functions=[],  # allow custom handling
            address=address,  # listen address
            framer=args.framer,  # The framer strategy to use
            # handler=None,  # handler for each session
            allow_reuse_address=True,  # allow the reuse of an address
            certfile=f"{path}/certificates/pymodbus.crt",  # The cert file path for TLS (used if sslctx is None)
            # sslctx=sslctx,  # The SSLContext to use for TLS (default None and auto create)
            keyfile=f"{path}/certificates/pymodbus.key",  # The key file path for TLS (used if sslctx is None)
            # password="none",  # The password for for decrypting the private key file
            # reqclicert=False,  # Force the sever request client"s certificate
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
            defer_start=False,  # Only define server do not activate
        )
    return server


if __name__ == "__main__":
    cmd_args = get_commandline(
        server=True,
        description="Run asynchronous server.",
    )
    run_args = setup_server(cmd_args)
    asyncio.run(run_async_server(run_args), debug=True)
