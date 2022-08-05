"""Initialize client.

import external classes, to make them easier to use:
"""
from pymodbus.client.async_udp import AsyncModbusUDPClient
from pymodbus.client.async_tls import AsyncModbusTLSClient
from pymodbus.client.async_serial import AsyncModbusSerialClient
from pymodbus.client.async_tcp import AsyncModbusTCPClient
from pymodbus.client.sync_serial import ModbusSerialClient
from pymodbus.client.sync_tcp import ModbusTcpClient
from pymodbus.client.sync_tls import ModbusTlsClient
from pymodbus.client.sync_udp import ModbusUdpClient

# ---------------------------------------------------------------------------#
#  Exported symbols
# ---------------------------------------------------------------------------#
__all__ = [
    "AsyncModbusUDPClient",
    "AsyncModbusTLSClient",
    "AsyncModbusSerialClient",
    "AsyncModbusTCPClient",
    "ModbusSerialClient",
    "ModbusTcpClient",
    "ModbusTlsClient",
    "ModbusUdpClient",
]
