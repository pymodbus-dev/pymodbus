#!/usr/bin/env python3
"""Pymodbus asynchronous Server Example.

An example of a multi threaded asynchronous server.

usage::

    server_async.py [-h] [--comm {tcp,udp,serial,tls}]
                    [--framer {ascii,rtu,socket,tls}]
                    [--log {critical,error,warning,info,debug}]
                    [--port PORT]
                    [--baudrate BAUDRATE]
                    [--device_ids DEVICE_IDS]

    -h, --help
        show this help message and exit
    -c, --comm {tcp,udp,serial,tls}
        set communication, default is tcp
    -f, --framer {ascii,rtu,socket,tls}
        set framer, default depends on --comm
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -p, --port PORT
        set port
    --baudrate BAUDRATE
        set serial device baud rate
    --device_ids DEVICE IDs
        set list of devices to respond to

The corresponding client can be started as:

    python3 client_sync.py

"""
import asyncio
import logging
import sys


try:
    import helper  # type: ignore[import-not-found]
except ImportError:
    print("*** ERROR --> THIS EXAMPLE needs to be run in the example directory, please see \n\
          https://pymodbus.readthedocs.io/en/latest/source/examples.html\n\
          for more information.")
    sys.exit(-1)

from pymodbus import ModbusDeviceIdentification
from pymodbus import __version__ as pymodbus_version
from pymodbus.server import (
    StartAsyncSerialServer,
    StartAsyncTcpServer,
    StartAsyncTlsServer,
    StartAsyncUdpServer,
)
from pymodbus.simulator import DataType, SimData, SimDevice


_logger = logging.getLogger(__file__)


def setup_server(description=None, context=None, cmdline=None):
    """Run server setup."""
    args = helper.get_commandline(server=True, description=description, cmdline=cmdline)
    if context:  # pragma: no cover
        args.context = context
    if not args.context:  # pragma: no cover
        _logger.info("### Create datastore")

        # Build data storage
        if args.device_ids > 1:  # pragma: no cover
            args.context = [SimDevice(device_id, SimData(0, datatype=DataType.REGISTERS, values=[17]*100))
                            for device_id in range(args.device_ids)]
        else:
            args.context = SimDevice(0, SimData(0, datatype=DataType.REGISTERS, values=[17]*100))

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
            "MajorMinorRevision": pymodbus_version,
        }
    )
    return args


async def run_async_server(args) -> None:
    """Run server."""
    txt = f"### start ASYNC server, listening on {args.port} - {args.comm}"
    _logger.info(txt)
    if args.comm == "tcp":
        address = (args.host if args.host else "", args.port if args.port else None)
        await StartAsyncTcpServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # ignore_missing_devices=True,  # ignore request to a missing device
            # broadcast_enable=False,  # treat device 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
        )
    elif args.comm == "udp":
        address = (
            args.host if args.host else "127.0.0.1",
            args.port if args.port else None,
        )
        await StartAsyncUdpServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # ignore_missing_devices=True,  # ignore request to a missing device
            # broadcast_enable=False,  # treat device id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
        )
    elif args.comm == "serial":
        # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600
        #             PTY,link=/tmp/ttyp0,raw,echo=0,ospeed=9600
        await StartAsyncSerialServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            # timeout=1,  # waiting time for request to complete
            port=args.port,  # serial port
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # stopbits=1,  # The number of stop bits to use
            # bytesize=8,  # The bytesize of the serial messages
            # parity="N",  # Which kind of parity to use
            baudrate=args.baudrate,  # The baud rate to use for the serial device
            # handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            # ignore_missing_devices=True,  # ignore request to a missing device
            # broadcast_enable=False,  # treat device_id 0 as broadcast address,
        )
    elif args.comm == "tls":  # pragma: no cover
        address = (args.host if args.host else "", args.port if args.port else None)
        await StartAsyncTlsServer(
            context=args.context,  # Data storage
            # port=port,  # on which port
            identity=args.identity,  # server identify
            # custom_functions=[],  # allow custom handling
            address=address,  # listen address
            framer=args.framer,  # The framer strategy to use
            certfile=helper.get_certificate(
                "crt"
            ),  # The cert file path for TLS (used if sslctx is None)
            # sslctx=sslctx,  # The SSLContext to use for TLS (default None and auto)
            keyfile=helper.get_certificate(
                "key"
            ),  # The key file path for TLS (used if sslctx is None)
            # password="none",  # The password for for decrypting the private key file
            # ignore_missing_devices=True,  # ignore request to a missing device
            # broadcast_enable=False,  # treat device_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
        )


async def async_helper() -> None:  # pragma: no cover
    """Combine setup and run."""
    _logger.info("Starting...")
    run_args = setup_server(description="Run asynchronous server.")
    await run_async_server(run_args)


if __name__ == "__main__":
    asyncio.run(async_helper(), debug=True)
