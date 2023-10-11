#!/usr/bin/env python3
"""Pymodbus Synchronous Server Example.

An example of a single threaded synchronous server.

usage::

    server_sync.py [-h] [--comm {tcp,udp,serial,tls}]
                   [--framer {ascii,binary,rtu,socket,tls}]
                   [--log {critical,error,warning,info,debug}]
                   [--port PORT] [--store {sequential,sparse,factory,none}]
                   [--slaves SLAVES]

    -h, --help
        show this help message and exit
    -c, --comm {tcp,udp,serial,tls}
        set communication, default is tcp
    -f, --framer {ascii,binary,rtu,socket,tls}
        set framer, default depends on --comm
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -p, --port PORT
        set port
        set serial device baud rate
    --store {sequential,sparse,factory,none}
        set datastore type
    --slaves SLAVES
        set number of slaves to respond to

The corresponding client can be started as:
    python3 client_sync.py

**REMARK** It is recommended to use the async server! The sync server
is just a thin cover on top of the async server and is in some aspects
a lot slower.
"""
import logging

from examples import helper
from examples.server_async import setup_server

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.server import (
    StartSerialServer,
    StartTcpServer,
    StartTlsServer,
    StartUdpServer,
)


_logger = logging.getLogger(__name__)
_logger.setLevel("DEBUG")


def run_sync_server(args):
    """Run server."""
    txt = f"### start SYNC server, listening on {args.port} - {args.comm}"
    _logger.info(txt)
    if args.comm == "tcp":
        address = ("", args.port) if args.port else None
        server = StartTcpServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            # TBD host=
            # TBD port=
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat slave_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "udp":
        address = ("127.0.0.1", args.port) if args.port else None
        server = StartUdpServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat slave_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "serial":
        # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600
        #             PTY,link=/tmp/ttyp0,raw,echo=0,ospeed=9600
        server = StartSerialServer(
            context=args.context,  # Data storage
            identity=args.identity,  # server identify
            # timeout=1,  # waiting time for request to complete
            port=args.port,  # serial port
            # custom_functions=[],  # allow custom handling
            framer=args.framer,  # The framer strategy to use
            # stopbits=1,  # The number of stop bits to use
            # bytesize=7,  # The bytesize of the serial messages
            # parity="E",  # Which kind of parity to use
            baudrate=args.baudrate,  # The baud rate to use for the serial device
            # handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat slave_id 0 as broadcast address,
            # strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "tls":  # pragma no cover
        address = ("", args.port) if args.port else None
        server = StartTlsServer(
            context=args.context,  # Data storage
            host="localhost",  # define tcp address where to connect to.
            # port=port,  # on which port
            identity=args.identity,  # server identify
            # custom_functions=[],  # allow custom handling
            address=address,  # listen address
            framer=args.framer,  # The framer strategy to use
            certfile=helper.get_certificate(
                "crt"
            ),  # The cert file path for TLS (used if sslctx is None)
            # sslctx=None,  # The SSLContext to use for TLS (default None and auto create)
            keyfile=helper.get_certificate(
                "key"
            ),  # The key file path for TLS (used if sslctx is None)
            # password=None,  # The password for for decrypting the private key file
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat slave_id 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    return server


def sync_helper():
    """Combine setup and run."""
    run_args = setup_server(description="Run synchronous server.")
    server = run_sync_server(run_args)
    server.shutdown()


if __name__ == "__main__":
    sync_helper()  # pragma: no cover
