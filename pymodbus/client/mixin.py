"""Modbus Client Common."""
from typing import Union, List
import logging

from pymodbus.constants import Defaults

import pymodbus.bit_read_message as pdu_bit_read
import pymodbus.bit_write_message as pdu_bit_write
import pymodbus.register_read_message as pdu_reg_read
import pymodbus.register_write_message as pdu_req_write
import pymodbus.other_message as pdu_other_msg
from pymodbus.utilities import ModbusTransactionState
from pymodbus.pdu import ModbusResponse, ModbusRequest
from pymodbus.exceptions import ModbusException

_logger = logging.getLogger(__name__)


class ModbusClientMixin:
    """**ModbusClientMixin**.

    Simple modbus message call::

        response = client.read_coils(1, 10)
        # or
        response = await client.read_coils(1, 10)

    Advanced modbus message call::

        request = ReadCoilsRequest(1,10)
        response = client.execute(request)
        # or
        request = ReadCoilsRequest(1,10)
        response = await client.execute(request)

    .. tip::
        All methods can be used directly (synchronous) or with await <method>
        depending on the instantiated client.
    """

    state = ModbusTransactionState.IDLE
    last_frame_end = 0
    silent_interval = 0

    def execute(self, request: ModbusRequest) -> ModbusResponse:
        """Execute request.

        :param request: Request to send
        :raises ModbusException:
        """
        raise ModbusException(f"Execute({request}) not implemented.")

    def read_coils(
        self,
        address: int,
        count: int = Defaults.Count,
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_bit_read.ReadCoilsResponse:
        """Read coils (function code 0x01).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_bit_read.ReadCoilsRequest(address, count, slave, **kwargs)
        return self.execute(request)

    def read_discrete_inputs(
        self,
        address: int,
        count: int = Defaults.Count,
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_bit_read.ReadDiscreteInputsResponse:
        """Read discrete inputs (function code 0x02).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_bit_read.ReadDiscreteInputsRequest(address, count, slave, **kwargs)
        return self.execute(request)

    def read_holding_registers(
        self,
        address: int,
        count: int = Defaults.Count,
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_reg_read.ReadHoldingRegistersResponse:
        """Read holding registers (function code 0x03).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_reg_read.ReadHoldingRegistersRequest(address, count, slave, **kwargs)
        return self.execute(request)

    def read_input_registers(
        self,
        address: int,
        count: int = Defaults.Count,
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_reg_read.ReadInputRegistersResponse:
        """Read input registers (function code 0x04).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_reg_read.ReadInputRegistersRequest(address, count, slave, **kwargs)
        return self.execute(request)

    def write_coil(
        self,
        address: int,
        value: bool,
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_bit_write.WriteSingleCoilResponse:
        """Write single coil (function code 0x05).

        :param address: Start address to read from
        :param value: Boolean to write
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_bit_write.WriteSingleCoilRequest(address, value, slave, **kwargs)
        return self.execute(request)

    def write_register(
        self,
        address: int,
        value: Union[int, float, str],
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_req_write.WriteSingleRegisterResponse:
        """Write register (function code 0x06).

        :param address: Start address to read from
        :param value: Value to write
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_req_write.WriteSingleRegisterRequest(address, value, slave, **kwargs)
        return self.execute(request)

    def read_exception_status(
        self,
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_other_msg.ReadExceptionStatusResponse:
        """Read Exception Status (Serial Line only) (function code 0x07).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_other_msg.ReadExceptionStatusRequest(slave, **kwargs)
        return self.execute(request)

    # TBD missing functions

    # Function codes descriptions
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

    def write_coils(
        self,
        address: int,
        values: List[bool],
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_bit_write.WriteMultipleCoilsResponse:
        """Write coils (function code 0x0F).

        :param address: Start address to read from
        :param values: List of booleans to write
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_bit_write.WriteMultipleCoilsRequest(address, values, slave, **kwargs)
        return self.execute(request)

    def write_registers(
        self,
        address: int,
        values: List[Union[int, float, str]],
        slave: int = Defaults.Slave,
        **kwargs: any
    ) -> pdu_req_write.WriteMultipleRegistersResponse:
        """Write registers (function code 0x10).

        :param address: Start address to read from
        :param values: List of booleans to write
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        request = pdu_req_write.WriteMultipleRegistersRequest(address, values, slave, **kwargs)
        return self.execute(request)

    # Function codes descriptions
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

    def readwrite_registers(self, *args, **kwargs) -> pdu_reg_read.ReadWriteMultipleRegistersResponse:
        """Read/Write registers

        :param args:
        :param kwargs:
        :returns: A deferred response handle
        """
        request = pdu_reg_read.ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)

    def mask_write_register(self, *args, **kwargs) -> pdu_req_write.MaskWriteRegisterResponse:
        """Mask write register.

        :args:
        :returns: A deferred response handle
        """
        request = pdu_req_write.MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)
