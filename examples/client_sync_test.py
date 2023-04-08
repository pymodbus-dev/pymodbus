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
  --baudrate BAUDRATE   the baud rate to use for the serial device

The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
import logging

import pymodbus.bit_read_message as pdu_bit_read
import pymodbus.bit_write_message as pdu_bit_write

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from examples.helper import get_commandline
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException


_logger = logging.getLogger()


def run_sync_client():
    """Run sync client."""
    args = get_commandline()
    _logger.info("### Create client object")
    client = ModbusTcpClient(
        args.host,
        port=args.port,
        framer=args.framer,
    )

    _logger.info("### Client starting")
    client.connect()

    _logger.info("### first read_coils to secure it works generally")
    try:
        rr = client.read_coils(1, 1, slave=1)
    except ModbusException as exc:
        _logger.error(exc)
        raise RuntimeError(exc) from exc
    if rr.isError():
        raise RuntimeError("ERROR: read_coils returned an error!")
    assert isinstance(rr, pdu_bit_read.ReadCoilsResponse)

    _logger.info("### next write_coil to change a value")
    try:
        rr = client.write_coil(1, 17, slave=1)
    except ModbusException as exc:
        _logger.error(exc)
        raise RuntimeError(exc) from exc
    if rr.isError():
        raise RuntimeError("ERROR: write_coil returned an error!")
    assert isinstance(rr, pdu_bit_write.WriteSingleCoilResponse)

    _logger.info("### finally read_coil to verify value")
    try:
        rr = client.read_coils(1, 1, slave=1)
    except ModbusException as exc:
        _logger.error(exc)
        raise RuntimeError(exc) from exc
    if rr.isError():
        raise RuntimeError("ERROR: read_coils(2) returned an error!")
    assert isinstance(rr, pdu_bit_read.ReadCoilsResponse)

    client.close()
    _logger.info("### End of Program")


if __name__ == "__main__":
    run_sync_client()
