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
import argparse
import asyncio
from threading import Thread
import logging


# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


def setup_async_client(loop):
    """Run client setup."""
    args = get_commandline()
    _logger.info("### Create client object")

    if args.comm == "tcp":
        client = AsyncModbusTCPClient(
            host="127.0.0.1",  # define tcp address where to connect to.
            port=args.port,  # on which port
            framer=ModbusSocketFramer,  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            source_address=("localhost", 0),  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
            loop=loop,
        )
    elif args.comm == "udp":
        client = AsyncModbusUDPClient(
            host="localhost",  # define tcp address where to connect to.
            port=args.port,  # on which port
            framer=args.framer,  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            source_address=("localhost", 0),  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
            loop=loop,
        )
    elif args.comm == "serial":
        client = AsyncModbusSerialClient(
            port=args.port,  # serial port
            framer=args.framer,  # how to interpret the messages
            stopbits=1,  # The number of stop bits to use
            bytesize=7,  # The bytesize of the serial messages
            parity="even",  # Which kind of parity to use
            baudrate=9600,  # The baud rate to use for the serial device
            handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            timeout=1,  # waiting time for request to complete
            strict=True,  # use strict timing, t1.5 for Modbus RTU
            loop=loop,
        )
    elif args.comm == "tls":
        client = AsyncModbusTLSClient(
            host="localhost",  # define tcp address where to connect to.
            port=args.port,  # on which port
            sslctx=None,  # ssl control
            certfile=None,  # certificate file
            keyfile=None,  # key file
            password=None,  # pass phrase
            framer=args.framer,  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            source_address=("localhost", 0),  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
            loop=loop,
        )
    return loop, client


async def run_async_client(modbus_calls=None):
    """Run sync client."""
    _logger.info("### Client ready")

    def done(future):  # pylint: disable=unused-argument
        """Done."""
        _logger.info("Done !!!")

    def start_loop(loop):
        """Start Loop"""
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    mythread = Thread(target=start_loop, args=[loop])
    mythread.daemon = True
    # Start the loop
    mythread.start()
    await asyncio.sleep(1)
    assert loop.is_running()  # nosec
    asyncio.set_event_loop(loop)

    loop, client = setup_async_client(loop)

    # Run supplied modbus calls
    if modbus_calls:
        future = asyncio.run_coroutine_threadsafe(
            modbus_calls(client.protocol), loop=loop
        )
    future.add_done_callback(done)
    while not future.done():
        await asyncio.sleep(0.1)
    loop.stop()
    _logger.info("### End of Program")


# --------------------------------------------------------------------------- #
# Extra code, to allow commandline parameters instead of changing the code
# --------------------------------------------------------------------------- #
FORMAT = "%(asctime)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
logging.basicConfig(format=FORMAT)
_logger = logging.getLogger()


def get_commandline():
    """Read and validate command line arguments"""
    parser = argparse.ArgumentParser(
        description="Connect/disconnect a synchronous client."
    )
    parser.add_argument(
        "--comm",
        choices=["tcp", "udp", "serial", "tls"],
        help='"serial", "tcp", "udp" or "tls"',
        type=str,
    )
    parser.add_argument(
        "--framer",
        choices=["ascii", "binary", "rtu", "socket", "tls"],
        help='"ascii", "binary", "rtu", "socket" or "tls"',
        type=str,
    )
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
    args = parser.parse_args()

    # set defaults
    comm_defaults = {
        "tcp": ["socket", 5020],
        "udp": ["socket", 5020],
        "serial": ["rtu", "/dev/ptyp0"],
        "tls": ["tls", 5020],
    }
    framers = {
        "ascii": ModbusAsciiFramer,
        "binary": ModbusBinaryFramer,
        "rtu": ModbusRtuFramer,
        "socket": ModbusSocketFramer,
        "tls": ModbusTlsFramer,
    }
    _logger.setLevel(args.log.upper() if args.log else logging.INFO)
    if not args.comm:
        args.comm = "tcp"
    if not args.framer:
        args.framer = comm_defaults[args.comm][0]
    if not args.port:
        args.port = comm_defaults[args.comm][1]
    args.framer = framers[args.framer]
    return args


if __name__ == "__main__":
    # Connect/disconnect no calls.
    asyncio.run(run_async_client())
