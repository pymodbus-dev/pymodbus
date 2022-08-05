#!/usr/bin/env python3
"""Pymodbus Synchronous Client Example.

An example of a single threaded synchronous client.

usage: client_sync.py [-h] [--comm {tcp,udp,serial,tls}]
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
import logging

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client import (
    ModbusSerialClient,
    ModbusTcpClient,
    ModbusTlsClient,
    ModbusUdpClient,
)
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


def setup_sync_client():
    """Run client setup."""
    args = get_commandline()
    args.comm = "serial"
    _logger.info("### Create client object")
    if args.comm == "tcp":
        client = ModbusTcpClient(
            host="127.0.0.1",  # define tcp address where to connect to.
            port=args.port,  # on which port
            framer=args.framer,  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            source_address=("localhost", 0),  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "udp":
        client = ModbusUdpClient(
            host="localhost",  # define tcp address where to connect to.
            port=args.port,  # on which port
            framer=args.framer,  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            source_address=("localhost", 0),  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "serial":
        client = ModbusSerialClient(
            port=args.port,  # serial port
            framer=args.framer,  # how to interpret the messages
            stopbits=1,  # The number of stop bits to use
            bytesize=7,  # The bytesize of the serial messages
            parity="E",  # Which kind of parity to use
            baudrate=9600,  # The baud rate to use for the serial device
            handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            timeout=1,  # waiting time for request to complete
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "tls":
        client = ModbusTlsClient(
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
        )
    return client, args.comm != "udp"


def run_sync_client(modbus_calls=None):
    """Run sync client."""
    client, do_connect = setup_sync_client()

    if do_connect:
        _logger.info("### Connect to server")
        client.connect()

    _logger.info("### Client ready")

    # Run supplied modbus calls
    if modbus_calls:
        modbus_calls(client)

    if do_connect:
        _logger.info("### Close connection to server")
        client.close()
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
    run_sync_client()
