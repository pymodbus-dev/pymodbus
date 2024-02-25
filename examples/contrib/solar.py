#!/usr/bin/env python3
"""Pymodbus Synchronous Client Example.

Modified to test long term connection.

"""
import logging
from time import sleep

from pymodbus import pymodbus_apply_logging_config

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.transaction import ModbusSocketFramer


_logger = logging.getLogger(__file__)
_logger.setLevel(logging.DEBUG)


def main():
    """Run client setup."""
    pymodbus_apply_logging_config(logging.DEBUG)
    _logger.info("### Client starting")
    client = ModbusTcpClient(
        "modbusServer.lan",
        port=502,
        # Common optional parameters:
        framer=ModbusSocketFramer,
        timeout=1,
        retry_on_empty=True,
    )
    client.connect()
    _logger.info("### Client connected")
    sleep(5)
    _logger.info("### Client starting")
    sleep_time = 2
    for count in range(int(60 / sleep_time) * 60 * 3):  # 3 hours
        _logger.info(f"Running loop {count}")
        solar_calls(client)
        sleep(sleep_time)  # scan_interval
    client.close()
    _logger.info("### End of Program")


def solar_calls(client):
    """Test connection works."""
    for addr, count in (
        (32008, 1),
        (32009, 1),
        (32010, 1),
        (32016, 1),
        (32017, 1),
        (32018, 1),
        (32019, 1),
        (32064, 2),
        (32078, 2),
        (32080, 2),
        (32114, 2),
        (37113, 2),
        (32078, 2),
        (32078, 2),
    ):
        lazy_error_count = 15
        while lazy_error_count > 0:
            try:
                rr = client.read_coils(addr, count, slave=1)
            except ModbusException as exc:
                _logger.debug(f"TEST: exception lazy({lazy_error_count}) {exc}")
                lazy_error_count -= 1
                continue
            if not hasattr(rr, "registers"):
                _logger.debug(f"TEST: no registers lazy({lazy_error_count})")
                lazy_error_count -= 1
                continue
            break
        if not lazy_error_count:
            raise RuntimeError("HARD ERROR, more than 15 retries!")


if __name__ == "__main__":
    main()
