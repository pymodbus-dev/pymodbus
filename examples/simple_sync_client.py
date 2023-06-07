#!/usr/bin/env python3
"""Pymodbus synchronous client example.

An example of a single threaded synchronous client.

usage: simple_client_async.py

All options must be adapted in the code
The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus import pymodbus_apply_logging_config
from pymodbus.client import (
    ModbusSerialClient,
    ModbusTcpClient,
    ModbusTlsClient,
    ModbusUdpClient,
)
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus.transaction import (
    #    ModbusAsciiFramer,
    #    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


def run_sync_client():
    """Run sync client."""

    # activate debugging
    pymodbus_apply_logging_config("DEBUG")

    # change to test other client types
    select_my_client = "tcp"

    print("get client")
    if select_my_client == "tcp":
        client = ModbusTcpClient(
            "127.0.0.1",  # host
            port=5020,
            framer=ModbusSocketFramer,
            # timeout=10,
            # retries=3,
            # retry_on_empty=False,y
            # close_comm_on_error=False,
            # strict=True,
            # source_address=("localhost", 0),
        )
    elif select_my_client == "tcp":
        client = ModbusUdpClient(
            "127.0.0.1",  # host
            port=5020,
            framer=ModbusSocketFramer,
            # timeout=10,
            # retries=3,
            # retry_on_empty=False,
            # close_comm_on_error=False,
            # strict=True,
            # source_address=None,
        )
    elif select_my_client == "serial":
        client = ModbusSerialClient(
            "/dev/tty01",  # tty port
            framer=ModbusRtuFramer,
            # timeout=10,
            # retries=3,
            # retry_on_empty=False,
            # close_comm_on_error=False,.
            # strict=True,
            baudrate=9600,
            # bytesize=8,
            # parity="N",
            # stopbits=1,
            # handle_local_echo=False,
        )
    elif select_my_client == "tls":
        client = ModbusTlsClient(
            "127.0.0.1",  # host
            port=5020,
            framer=ModbusTlsFramer,
            # timeout=10,
            # retries=3,
            # retry_on_empty=False,
            # close_comm_on_error=False,
            # strict=True,
            # sslctx=None,
            certfile="my_cert.crt",
            keyfile="my_cert.key",
            # password=None,
            server_hostname="localhost",
        )
    else:
        print(f"Unknown client {select_my_client} selected")
        return

    print("connect to server")
    client.connect()

    print("get and verify data")
    try:
        rr = client.read_coils(1, 1, slave=1)
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        client.close()
        return
    if rr.isError():
        print(f"Received Modbus library error({rr})")
        client.close()
        return
    if isinstance(rr, ExceptionResponse):
        print(f"Received Modbus library exception ({rr})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        client.close()

    print("close connection")
    client.close()


if __name__ == "__main__":
    run_sync_client()
