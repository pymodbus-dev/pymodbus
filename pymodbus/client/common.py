"""Modbus Client Common.

This is a common client mixin that can be used by
both the synchronous and asynchronous clients to
simplify the interface.
"""
from pymodbus.bit_read_message import (
    ReadCoilsRequest,
    ReadDiscreteInputsRequest,
)
from pymodbus.bit_write_message import (
    WriteSingleCoilRequest,
    WriteMultipleCoilsRequest,
)
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadInputRegistersRequest,
    ReadWriteMultipleRegistersRequest,
)
from pymodbus.register_write_message import (
    WriteSingleRegisterRequest,
    WriteMultipleRegistersRequest,
    MaskWriteRegisterRequest,
)
from pymodbus.utilities import ModbusTransactionState


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

    def read_coils(self, address, count=1, **kwargs):
        """Read coils.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = ReadCoilsRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_discrete_inputs(self, address, count=1, **kwargs):
        """Read discrete inputs.

        :param address: The starting address to read from
        :param count: The number of discretes to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = ReadDiscreteInputsRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_coil(self, address, value, **kwargs):
        """Write_coil.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = WriteSingleCoilRequest(address, value, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_coils(self, address, values, **kwargs):
        """Write coils.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = WriteMultipleCoilsRequest(address, values, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_register(self, address, value, **kwargs):
        """Write register.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = WriteSingleRegisterRequest(address, value, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_registers(self, address, values, **kwargs):
        """Write registers.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = WriteMultipleRegistersRequest(address, values, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_holding_registers(self, address, count=1, **kwargs):
        """Read holding registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = ReadHoldingRegistersRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_input_registers(self, address, count=1, **kwargs):
        """Read input registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = ReadInputRegistersRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def readwrite_registers(self, *args, **kwargs):
        """Read/Write registers

        :param read_address: The address to start reading from
        :param read_count: The number of registers to read from address
        :param write_address: The address to start writing to
        :param write_registers: The registers to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def mask_write_register(self, *args, **kwargs):
        """Mask write register.

        :param address: The address of the register to write
        :param and_mask: The and bitmask to apply to the register address
        :param or_mask: The or bitmask to apply to the register address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        """
        request = MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)  # pylint: disable=no-member


# ---------------------------------------------------------------------------#
#  Exported symbols
# ---------------------------------------------------------------------------#
__all__ = ["ModbusClientMixin"]
