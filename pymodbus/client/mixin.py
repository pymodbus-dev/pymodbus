"""Modbus Client Common.

This is a common client mixin that can be used by
both the synchronous and asynchronous clients to
simplify the interface.
"""

# Function codes descriptions
# 0x01 Read Coils
# 0x02 Read Discrete Inputs
# 0x03 Read Holding Registers
# 0x04 Read Input Registers
# 0x05 Write Single Coil
# 0x06 Write Single Register
# 0x07 Read Exception Status (Serial Line only)
# 0x08 Diagnostics (Serial Line only)
#     Sub-function codes supported by the serial line devices
#         0x00 Return Query Data
#         0x01 Restart Communications Option
#         0x02 Return Diagnostic Register
#         0x03 Change ASCII Input Delimiter
#         0x04 Force Listen Only Mode
#         0x05 - 0x09 RESERVED
#         0x0A Clear Counters and Diagnostic Register
#         0x0B Return Bus Message Count
#         0x0C Return Bus Communication Error Count
#         0x0D Return Bus Exception Error Count
#         0x0E Return Slave Message Count
#         0x0F Return Slave No Response Count
#         0x10 Return Slave NAK Count
#         0x11 Return Slave Busy Count
#         0x12 Return Bus Character Overrun Count
#         0x13 RESERVED
#         0x14 Clear Overrun Counter and Flag
#         0x15 RESERVED
# 0x0B Get Comm Event Counter (Serial Line only)
# 0x0C Get Comm Event Log (Serial Line only)
# 0x0F Write Multiple Coils
# 0x10 Write Multiple registers
# 0x11 Report Slave ID (Serial Line only)
# 0x14 Read File Record
# 0x15 Write File Record
# 0x16 Mask Write Register
# 0x17 Read/Write Multiple registers
# 0x18 Read FIFO Queue
# 0x2B Encapsulated Interface Transport
# 0x2B / 0x0D CANopen General Reference Request and Response
#     PDU
# 0x2B / 0x0E Read Device Identification
# MODBUS Exception Responses
# Annex A (Informative)
# Annex B (Informative)

# pylint: disable=missing-type-doc
import logging

from pymodbus.bit_read_message import ReadCoilsRequest, ReadDiscreteInputsRequest
from pymodbus.bit_write_message import WriteMultipleCoilsRequest, WriteSingleCoilRequest
from pymodbus.constants import Defaults
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadInputRegistersRequest,
    ReadWriteMultipleRegistersRequest,
)
from pymodbus.register_write_message import (
    MaskWriteRegisterRequest,
    WriteMultipleRegistersRequest,
    WriteSingleRegisterRequest,
)
from pymodbus.utilities import ModbusTransactionState

_logger = logging.getLogger(__name__)


class ModbusClientMixin:
    """Modbus client mixin that provides additional factory methods.

    for all the current modbus methods. This can be used
    instead of the normal pattern of::

       # instead of this
       client = ModbusClient(...)
       request = ReadCoilsRequest(1,10)
       response = client.execute(request)

       # now like this
       client = ModbusClient(...)
       response = client.read_coils(1, 10)
    """

    state = ModbusTransactionState.IDLE
    last_frame_end = 0
    silent_interval = 0

    def read_coils(self, address, count=1, unit=Defaults.UnitId, **kwargs):
        """Read coils.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadCoilsRequest(address, count, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_discrete_inputs(self, address, count=1, unit=Defaults.UnitId, **kwargs):
        """Read discrete inputs.

        :param address: The starting address to read from
        :param count: The number of discretes to read
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadDiscreteInputsRequest(address, count, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_coil(self, address, value, unit=Defaults.UnitId, **kwargs):
        """Write_coil.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteSingleCoilRequest(address, value, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_coils(self, address, values, unit=Defaults.UnitId, **kwargs):
        """Write coils.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteMultipleCoilsRequest(address, values, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_register(self, address, value, unit=Defaults.UnitId, **kwargs):
        """Write register.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteSingleRegisterRequest(address, value, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_registers(self, address, values, unit=Defaults.UnitId, **kwargs):
        """Write registers.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteMultipleRegistersRequest(address, values, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_holding_registers(self, address, count=1, unit=Defaults.UnitId, **kwargs):
        """Read holding registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadHoldingRegistersRequest(address, count, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_input_registers(self, address, count=1, unit=Defaults.UnitId, **kwargs):
        """Read input registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: Modbus slave unit ID
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadInputRegistersRequest(address, count, unit, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def readwrite_registers(self, *args, **kwargs):
        """Read/Write registers

        :param args:
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def mask_write_register(self, *args, **kwargs):
        """Mask write register.

        :args:
        :returns: A deferred response handle
        """
        request = MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)  # pylint: disable=no-member
