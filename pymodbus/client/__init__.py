"""Client.

import external classes, to make them easier to use:
"""
from pymodbus.client.serial import AsyncModbusSerialClient, ModbusSerialClient
from pymodbus.client.tcp import AsyncModbusTcpClient, ModbusTcpClient
from pymodbus.client.tls import AsyncModbusTlsClient, ModbusTlsClient
from pymodbus.client.udp import AsyncModbusUdpClient, ModbusUdpClient
from pymodbus.client.base import ModbusBaseClient


# ---------------------------------------------------------------------------#
#  Exported symbols
# ---------------------------------------------------------------------------#
__all__ = [
    "AsyncModbusSerialClient",
    "AsyncModbusTcpClient",
    "AsyncModbusTlsClient",
    "AsyncModbusUdpClient",
    "ModbusBaseClient",
    "ModbusSerialClient",
    "ModbusTcpClient",
    "ModbusTlsClient",
    "ModbusUdpClient",
]
