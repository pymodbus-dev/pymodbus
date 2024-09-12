#!/usr/bin/env python3
"""Pymodbus Synchronous Client Example.

Modified to test long term connection.

Modified to actually work with Huawei SUN2000 inverters, that better support async Modbus operations so errors will occur
Configure HOST (the IP address of the inverter as a string), PORT and CYCLES to fit your needs

"""
import logging
from enum import Enum
from math import log10
from time import sleep

from pymodbus import pymodbus_apply_logging_config

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus import FramerType


HOST = "modbusServer.lan"
PORT = 502
CYCLES = 4


pymodbus_apply_logging_config(logging.ERROR)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
_logger = logging.getLogger(__file__)


def main() -> None:
    """Run client setup."""
    _logger.info("### Client starting")
    client: ModbusTcpClient = ModbusTcpClient(
        host=HOST,
        port=PORT,
        # Common optional parameters:
        framer=FramerType.SOCKET,
        timeout=5,
    )
    client.connect()
    _logger.info("### Client connected")
    sleep(1)
    _logger.info("### Client starting")
    for count in range(CYCLES):
        _logger.info(f"Running loop {count}")
        solar_calls(client)
        sleep(10)  # scan interval
    client.close()
    _logger.info("### End of Program")


def solar_calls(client: ModbusTcpClient) -> None:
    """Read registers."""
    error = False
        
    for addr, format, factor, comment, unit in ( # data_type according to ModbusClientMixin.DATATYPE.value[0]
        (32008, "H", 1,     "Alarm 1",                          "(bitfield)"),
        (32009, "H", 1,     "Alarm 2",                          "(bitfield)"),
        (32010, "H", 1,     "Alarm 3",                          "(bitfield)"),
        (32016, "h", 0.1,   "PV 1 voltage",                     "V"),
        (32017, "h", 0.01,  "PV 1 current",                     "A"),
        (32018, "h", 0.1,   "PV 2 voltage",                     "V"),
        (32019, "h", 0.01,  "PV 2 current",                     "A"),
        (32064, "i", 0.001, "Input power",                      "kW"),
        (32078, "i", 0.001, "Peak active power of current day", "kW"),
        (32080, "i", 0.001, "Active power",                     "kW"),
        (32114, "I", 0.001, "Daily energy yield",               "kWh"),
    ):
        if error:
            error = False
            client.close()
            sleep(0.1)
            client.connect()
            sleep(1)
        
        data_type = get_data_type(format)
        count = data_type.value[1]
        var_type = data_type.name

        _logger.info(f"*** Reading {comment} ({var_type})")
        
        try:
            rr = client.read_holding_registers(address=addr, count=count, slave=1)
        except ModbusException as exc:
            _logger.error(f"Modbus exception: {exc!s}")
            error = True
            continue
        if rr.isError():
            _logger.error(f"Error")
            error = True
            continue
        if isinstance(rr, ExceptionResponse):
            _logger.error(f"Response exception: {rr!s}")
            error = True
            continue
        
        value = client.convert_from_registers(rr.registers, data_type) * factor
        if factor < 1:
            value = round(value, int(log10(factor) * -1))
        _logger.info(f"*** READ *** {comment} = {value} {unit}")


def get_data_type(format: str) -> Enum:
    """Return the ModbusTcpClient.DATATYPE according to the format"""
    for data_type in ModbusTcpClient.DATATYPE:
        if data_type.value[0] == format:
            return data_type


if __name__ == "__main__":
    main()
