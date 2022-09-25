"""Modbus Client Common."""
import logging
from typing import List, Union

import pymodbus.bit_read_message as pdu_bit_read
import pymodbus.bit_write_message as pdu_bit_write
from pymodbus.constants import Defaults
import pymodbus.diag_message as pdu_diag
import pymodbus.other_message as pdu_other_msg
from pymodbus.pdu import ModbusRequest, ModbusResponse
import pymodbus.register_read_message as pdu_reg_read
import pymodbus.register_write_message as pdu_req_write
from pymodbus.utilities import ModbusTransactionState


_logger = logging.getLogger(__name__)


class ModbusClientMixin:  # pylint: disable=too-many-public-methods
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
        return request

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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_bit_read.ReadDiscreteInputsRequest(
            address, count, slave, **kwargs
        )
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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_reg_read.ReadHoldingRegistersRequest(
            address, count, slave, **kwargs
        )
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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_reg_read.ReadInputRegistersRequest(
            address, count, slave, **kwargs
        )
        return self.execute(request)

    def write_coil(
        self, address: int, value: bool, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_bit_write.WriteSingleCoilResponse:
        """Write single coil (function code 0x05).

        :param address: Start address to read from
        :param value: Boolean to write
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_req_write.WriteSingleRegisterRequest(
            address, value, slave, **kwargs
        )
        return self.execute(request)

    def read_exception_status(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_other_msg.ReadExceptionStatusResponse:
        """Read Exception Status (function code 0x07).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_other_msg.ReadExceptionStatusRequest(slave, **kwargs)
        return self.execute(request)

    def diag_query_data(
        self, msg: bytearray, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnQueryDataResponse:
        """Diagnose query data (function code 0x08 - 0x00).

        :param msg: Message to be returned
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnQueryDataRequest(msg, slave, **kwargs)
        return self.execute(request)

    def diag_restart_communication(
        self, toggle: bool, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.RestartCommunicationsOptionResponse:
        """Diagnose restart communication (function code 0x08 - 0x01).

        :param toggle: True if toogled.
        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.RestartCommunicationsOptionRequest(toggle, slave, **kwargs)
        return self.execute(request)

    def diag_read_diagnostic_register(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnDiagnosticRegisterResponse:
        """Diagnose read diagnostic register (function code 0x08 - 0x02).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnDiagnosticRegisterRequest(slave, **kwargs)
        return self.execute(request)

    def diag_change_ascii_input_delimeter(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ChangeAsciiInputDelimiterResponse:
        """Diagnose change ASCII input delimiter (function code 0x08 - 0x03).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ChangeAsciiInputDelimiterRequest(slave, **kwargs)
        return self.execute(request)

    def diag_force_listen_only(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ForceListenOnlyModeResponse:
        """Diagnose force listen only (function code 0x08 - 0x04).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ForceListenOnlyModeRequest(slave, **kwargs)
        return self.execute(request)

    def diag_clear_counters(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ClearCountersResponse:
        """Diagnose clear counters (function code 0x08 - 0x0A).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ClearCountersRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_bus_message_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnBusMessageCountResponse:
        """Diagnose read bus message count (function code 0x08 - 0x0B).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnBusMessageCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_bus_comm_error_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnBusCommunicationErrorCountResponse:
        """Diagnose read Bus Communication Error Count (function code 0x08 - 0x0C).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnBusCommunicationErrorCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_bus_exception_error_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnBusExceptionErrorCountResponse:
        """Diagnose read Bus Exception Error Count (function code 0x08 - 0x0D).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnBusExceptionErrorCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_slave_message_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnSlaveMessageCountResponse:
        """Diagnose read Slave Message Count (function code 0x08 - 0x0E).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnSlaveMessageCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_slave_no_response_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnSlaveNoReponseCountResponse:
        """Diagnose read Slave No Response Count (function code 0x08 - 0x0F).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnSlaveNoResponseCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_slave_nak_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnSlaveNAKCountResponse:
        """Diagnose read Slave NAK Count (function code 0x08 - 0x10).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnSlaveNAKCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_slave_busy_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnSlaveBusyCountResponse:
        """Diagnose read Slave Busy Count (function code 0x08 - 0x11).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnSlaveBusyCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_bus_char_overrun_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnSlaveBusCharacterOverrunCountResponse:
        """Diagnose read Bus Character Overrun Count (function code 0x08 - 0x12).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnSlaveBusCharacterOverrunCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_read_iop_overrun_count(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ReturnIopOverrunCountResponse:
        """Diagnose read Iop overrun count (function code 0x08 - 0x13).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ReturnIopOverrunCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_clear_overrun_counter(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.ClearOverrunCountResponse:
        """Diagnose Clear Overrun Counter and Flag (function code 0x08 - 0x14).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.ClearOverrunCountRequest(slave, **kwargs)
        return self.execute(request)

    def diag_getclear_modbus_response(
        self, slave: int = Defaults.Slave, **kwargs: any
    ) -> pdu_diag.GetClearModbusPlusResponse:
        """Diagnose Get/Clear modbus plus request (function code 0x08 - 0x15).

        :param slave: (optional) Modbus slave unit ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_diag.GetClearModbusPlusRequest(slave, **kwargs)
        return self.execute(request)

    # TBD missing functions
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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_bit_write.WriteMultipleCoilsRequest(
            address, values, slave, **kwargs
        )
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
        if "unit" in kwargs:
            _logger.error("Please do not use unit=, convert to slave=.")
            slave = kwargs.pop("unit", slave)
        request = pdu_req_write.WriteMultipleRegistersRequest(
            address, values, slave, **kwargs
        )
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

    def readwrite_registers(
        self, *args, **kwargs
    ) -> pdu_reg_read.ReadWriteMultipleRegistersResponse:
        """Read/Write registers

        :param args:
        :param kwargs:
        :returns: A deferred response handle
        """
        request = pdu_reg_read.ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)

    def mask_write_register(
        self, *args, **kwargs
    ) -> pdu_req_write.MaskWriteRegisterResponse:
        """Mask write register.

        :args:
        :returns: A deferred response handle
        """
        request = pdu_req_write.MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)
