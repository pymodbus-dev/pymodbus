#!/usr/bin/env python3
"""Pymodbus Synchronous Client Example.

An example of a single threaded synchronous client.

usage: client_sync.py [-h] [-c {tcp,udp,serial,tls}]
                       [-f {ascii,binary,rtu,socket,tls}]
                       [-l {critical,error,warning,info,debug}] [-p PORT]
                       [--baudrate BAUDRATE] [--host HOST]

Run asynchronous client.

options:
  -h, --help            show this help message and exit
  -c {tcp,udp,serial,tls}, --comm {tcp,udp,serial,tls}
                        set communication, default is tcp
  -f {ascii,binary,rtu,socket,tls}, --framer {ascii,binary,rtu,socket,tls}
                        set framer, default depends on --comm
  -l {critical,error,warning,info,debug}, --log {critical,error,warning,info,debug}
                        set log level, default is info
  -p PORT, --port PORT  set port
  --baudrate BAUDRATE   set serial device baud rate
  --host HOST           set host, default is 127.0.0.1

The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
import logging

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from examples import helper
from pymodbus.client import (
    ModbusSerialClient,
    ModbusTcpClient,
    ModbusTlsClient,
    ModbusUdpClient,
)


_logger = logging.getLogger()
_logger.setLevel("DEBUG")


def setup_sync_client(description=None, cmdline=None):
    """Run client setup."""
    args = helper.get_commandline(
        server=False,
        description=description,
        cmdline=cmdline,
    )
    _logger.info("### Create client object")
    if args.comm == "tcp":
        client = ModbusTcpClient(
            args.host,
            port=args.port,
            # Common optional paramers:
            framer=args.framer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,y
            #    close_comm_on_error=False,
            #    strict=True,
            # TCP setup parameters
            #    source_address=("localhost", 0),
        )
    elif args.comm == "udp":
        client = ModbusUdpClient(
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
        client = ModbusSerialClient(
            port=args.port,  # serial port
            # Common optional paramers:
            #    framer=ModbusRtuFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,.
            #    strict=True,
            # Serial setup parameters
            baudrate=args.baudrate,
            #    bytesize=8,
            #    parity="N",
            #    stopbits=1,
            #    handle_local_echo=False,
        )
    elif args.comm == "tls":
        client = ModbusTlsClient(
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
            #    sslctx=None,
            certfile=helper.get_certificate("crt"),
            keyfile=helper.get_certificate("key"),
            #    password=None,
            server_hostname="localhost",
        )
    return client


def run_sync_client(client, modbus_calls=None):
    """Run sync client."""
    _logger.info("### Client starting")
    client.connect()
    if modbus_calls:
        modbus_calls(client)
    client.close()
    _logger.info("### End of Program")


def run_a_few_calls(client):
    """Test connection works."""
    rr = client.read_coils(32, 1, slave=1)
    assert len(rr.bits) == 8
    rr = client.read_holding_registers(4, 2, slave=1)
    assert rr.registers[0] == 17
    assert rr.registers[1] == 17


if __name__ == "__main__":
    testclient = setup_sync_client(description="Run synchronous client.")
    run_sync_client(testclient, modbus_calls=run_a_few_calls)
