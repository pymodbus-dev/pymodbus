"""Modbus Client Common."""
from __future__ import annotations

import struct
from enum import Enum
from typing import Any, Generic, TypeVar

import pymodbus.bit_read_message as pdu_bit_read
import pymodbus.bit_write_message as pdu_bit_write
import pymodbus.diag_message as pdu_diag
import pymodbus.file_message as pdu_file_msg
import pymodbus.mei_message as pdu_mei
import pymodbus.other_message as pdu_other_msg
import pymodbus.register_read_message as pdu_reg_read
import pymodbus.register_write_message as pdu_req_write
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ModbusRequest


T = TypeVar("T", covariant=False)


class ModbusClientMixin(Generic[T]):  # pylint: disable=too-many-public-methods
    """**ModbusClientMixin**.

    This is an interface class to facilitate the sending requests/receiving responses like read_coils.
    execute() allows to make a call with non-standard or user defined function codes (remember to add a PDU
    in the transport class to interpret the request/response).

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
        All methods can be used directly (synchronous) or
        with await <method> (asynchronous) depending on the client used.
    """

    def __init__(self):
        """Initialize."""

    def execute(self, _request: ModbusRequest) -> T:
        """Execute request (code ???).

        :raises ModbusException:

        Call with custom function codes.

        .. tip::
            Response is not interpreted.
        """
        raise NotImplementedError(
            "The execute method of ModbusClientMixin needs to be overridden and cannot be used directly"
        )

    def read_coils(
        self, address: int, count: int = 1, slave: int = 0, **kwargs: Any
    ) -> T:
        """Read coils (code 0x01).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_bit_read.ReadCoilsRequest(address, count, slave, **kwargs)
        )

    def read_discrete_inputs(
        self, address: int, count: int = 1, slave: int = 0, **kwargs: Any
    ) -> T:
        """Read discrete inputs (code 0x02).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_bit_read.ReadDiscreteInputsRequest(address, count, slave, **kwargs)
        )

    def read_holding_registers(
        self, address: int, count: int = 1, slave: int = 0, **kwargs: Any
    ) -> T:
        """Read holding registers (code 0x03).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_reg_read.ReadHoldingRegistersRequest(address, count, slave, **kwargs)
        )

    def read_input_registers(
        self, address: int, count: int = 1, slave: int = 0, **kwargs: Any
    ) -> T:
        """Read input registers (code 0x04).

        :param address: Start address to read from
        :param count: (optional) Number of coils to read
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_reg_read.ReadInputRegistersRequest(address, count, slave, **kwargs)
        )

    def write_coil(self, address: int, value: bool, slave: int = 0, **kwargs: Any) -> T:
        """Write single coil (code 0x05).

        :param address: Address to write to
        :param value: Boolean to write
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_bit_write.WriteSingleCoilRequest(address, value, slave, **kwargs)
        )

    def write_register(
        self, address: int, value: int, slave: int = 0, **kwargs: Any
    ) -> T:
        """Write register (code 0x06).

        :param address: Address to write to
        :param value: Value to write
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_req_write.WriteSingleRegisterRequest(address, value, slave, **kwargs)
        )

    def read_exception_status(self, slave: int = 0, **kwargs: Any) -> T:
        """Read Exception Status (code 0x07).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_other_msg.ReadExceptionStatusRequest(slave, **kwargs))


    def diag_query_data(
        self, msg: bytes, slave: int = 0, **kwargs: Any
    ) -> T:
        """Diagnose query data (code 0x08 sub 0x00).

        :param msg: Message to be returned
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.ReturnQueryDataRequest(msg, slave=slave, **kwargs))

    def diag_restart_communication(
        self, toggle: bool, slave: int = 0, **kwargs: Any
    ) -> T:
        """Diagnose restart communication (code 0x08 sub 0x01).

        :param toggle: True if toggled.
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.RestartCommunicationsOptionRequest(toggle, slave=slave, **kwargs)
        )

    def diag_read_diagnostic_register(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read diagnostic register (code 0x08 sub 0x02).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnDiagnosticRegisterRequest(slave=slave, **kwargs)
        )

    def diag_change_ascii_input_delimeter(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose change ASCII input delimiter (code 0x08 sub 0x03).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ChangeAsciiInputDelimiterRequest(slave=slave, **kwargs)
        )

    def diag_force_listen_only(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose force listen only (code 0x08 sub 0x04).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.ForceListenOnlyModeRequest(slave=slave, **kwargs))

    def diag_clear_counters(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose clear counters (code 0x08 sub 0x0A).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.ClearCountersRequest(slave=slave, **kwargs))

    def diag_read_bus_message_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read bus message count (code 0x08 sub 0x0B).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnBusMessageCountRequest(slave=slave, **kwargs)
        )

    def diag_read_bus_comm_error_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Bus Communication Error Count (code 0x08 sub 0x0C).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnBusCommunicationErrorCountRequest(slave=slave, **kwargs)
        )

    def diag_read_bus_exception_error_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Bus Exception Error Count (code 0x08 sub 0x0D).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnBusExceptionErrorCountRequest(slave=slave, **kwargs)
        )

    def diag_read_slave_message_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Slave Message Count (code 0x08 sub 0x0E).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnSlaveMessageCountRequest(slave=slave, **kwargs)
        )

    def diag_read_slave_no_response_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Slave No Response Count (code 0x08 sub 0x0F).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnSlaveNoResponseCountRequest(slave=slave, **kwargs)
        )

    def diag_read_slave_nak_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Slave NAK Count (code 0x08 sub 0x10).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.ReturnSlaveNAKCountRequest(slave=slave, **kwargs))

    def diag_read_slave_busy_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Slave Busy Count (code 0x08 sub 0x11).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.ReturnSlaveBusyCountRequest(slave=slave, **kwargs))

    def diag_read_bus_char_overrun_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Bus Character Overrun Count (code 0x08 sub 0x12).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnSlaveBusCharacterOverrunCountRequest(slave=slave, **kwargs)
        )

    def diag_read_iop_overrun_count(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose read Iop overrun count (code 0x08 sub 0x13).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_diag.ReturnIopOverrunCountRequest(slave=slave, **kwargs)
        )

    def diag_clear_overrun_counter(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose Clear Overrun Counter and Flag (code 0x08 sub 0x14).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.ClearOverrunCountRequest(slave=slave, **kwargs))

    def diag_getclear_modbus_response(self, slave: int = 0, **kwargs: Any) -> T:
        """Diagnose Get/Clear modbus plus (code 0x08 sub 0x15).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_diag.GetClearModbusPlusRequest(slave=slave, **kwargs))

    def diag_get_comm_event_counter(self, **kwargs: Any) -> T:
        """Diagnose get event counter (code 0x0B).

        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_other_msg.GetCommEventCounterRequest(**kwargs))

    def diag_get_comm_event_log(self, **kwargs: Any) -> T:
        """Diagnose get event counter (code 0x0C).

        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_other_msg.GetCommEventLogRequest(**kwargs))

    def write_coils(
        self,
        address: int,
        values: list[bool] | bool,
        slave: int = 0,
        **kwargs: Any,
    ) -> T:
        """Write coils (code 0x0F).

        :param address: Start address to write to
        :param values: List of booleans to write, or a single boolean to write
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_bit_write.WriteMultipleCoilsRequest(address, values, slave, **kwargs)
        )

    def write_registers(
        self, address: int, values: list[int] | int, slave: int = 0, **kwargs: Any
    ) -> T:
        """Write registers (code 0x10).

        :param address: Start address to write to
        :param values: List of values to write, or a single value to write
        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_req_write.WriteMultipleRegistersRequest(
                address, values, slave, **kwargs
            )
        )

    def report_slave_id(self, slave: int = 0, **kwargs: Any) -> T:
        """Report slave ID (code 0x11).

        :param slave: (optional) Modbus slave ID
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_other_msg.ReportSlaveIdRequest(slave, **kwargs))

    def read_file_record(self, records: list[tuple], **kwargs: Any) -> T:
        """Read file record (code 0x14).

        :param records: List of (Reference type, File number, Record Number, Record Length)
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_file_msg.ReadFileRecordRequest(records, **kwargs))

    def write_file_record(self, records: list[tuple], **kwargs: Any) -> T:
        """Write file record (code 0x15).

        :param records: List of (Reference type, File number, Record Number, Record Length)
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(pdu_file_msg.WriteFileRecordRequest(records, **kwargs))

    def mask_write_register(
        self,
        address: int = 0x0000,
        and_mask: int = 0xFFFF,
        or_mask: int = 0x0000,
        **kwargs: Any,
    ) -> T:
        """Mask write register (code 0x16).

        :param address: The mask pointer address (0x0000 to 0xffff)
        :param and_mask: The and bitmask to apply to the register address
        :param or_mask: The or bitmask to apply to the register address
        :param kwargs: (optional) Experimental parameters.
        :raises ModbusException:
        """
        return self.execute(
            pdu_req_write.MaskWriteRegisterRequest(address, and_mask, or_mask, **kwargs)
        )

    def readwrite_registers(
        self,
        read_address: int = 0,
        read_count: int = 0,
        write_address: int = 0,
        values: list[int] | int = 0,
        slave: int = 0,
        **kwargs,
    ) -> T:
        """Read/Write registers (code 0x17).

        :param read_address: The address to start reading from
        :param read_count: The number of registers to read from address
        :param write_address: The address to start writing to
        :param values: List of values to write, or a single value to write
        :param slave: (optional) Modbus slave ID
        :param kwargs:
        :raises ModbusException:
        """
        return self.execute(
            pdu_reg_read.ReadWriteMultipleRegistersRequest(
                read_address=read_address,
                read_count=read_count,
                write_address=write_address,
                write_registers=values,
                slave=slave,
                **kwargs,
            )
        )

    def read_fifo_queue(self, address: int = 0x0000, **kwargs: Any) -> T:
        """Read FIFO queue (code 0x18).

        :param address: The address to start reading from
        :param kwargs:
        :raises ModbusException:
        """
        return self.execute(pdu_file_msg.ReadFifoQueueRequest(address, **kwargs))

    # code 0x2B sub 0x0D: CANopen General Reference Request and Response, NOT IMPLEMENTED

    def read_device_information(
        self, read_code: int | None = None, object_id: int = 0x00, **kwargs: Any
    ) -> T:
        """Read FIFO queue (code 0x2B sub 0x0E).

        :param read_code: The device information read code
        :param object_id: The object to read from
        :param kwargs:
        :raises ModbusException:
        """
        return self.execute(
            pdu_mei.ReadDeviceInformationRequest(read_code, object_id, **kwargs)
        )

    # ------------------
    # Converter methods
    # ------------------

    class DATATYPE(Enum):
        """Datatype enum (name and number of bytes), used for convert_* calls."""

        INT16 = ("h", 1)
        UINT16 = ("H", 1)
        INT32 = ("i", 2)
        UINT32 = ("I", 2)
        INT64 = ("q", 4)
        UINT64 = ("Q", 4)
        FLOAT32 = ("f", 2)
        FLOAT64 = ("d", 4)
        STRING = ("s", 0)

    @classmethod
    def convert_from_registers(
        cls, registers: list[int], data_type: DATATYPE
    ) -> int | float | str:
        """Convert registers to int/float/str.

        :param registers: list of registers received from e.g. read_holding_registers()
        :param data_type: data type to convert to
        :returns: int, float or str depending on "data_type"
        :raises ModbusException: when size of registers is not 1, 2 or 4
        """
        byte_list = bytearray()
        for x in registers:
            byte_list.extend(int.to_bytes(x, 2, "big"))
        if data_type == cls.DATATYPE.STRING:
            if byte_list[-1:] == b"\00":
                byte_list = byte_list[:-1]
            return byte_list.decode("utf-8")
        if len(registers) != data_type.value[1]:
            raise ModbusException(
                f"Illegal size ({len(registers)}) of register array, cannot convert!"
            )
        return struct.unpack(f">{data_type.value[0]}", byte_list)[0]

    @classmethod
    def convert_to_registers(
        cls, value: int | float | str, data_type: DATATYPE
    ) -> list[int]:
        """Convert int/float/str to registers (16/32/64 bit).

        :param value: value to be converted
        :param data_type: data type to be encoded as registers
        :returns: List of registers, can be used directly in e.g. write_registers()
        :raises TypeError: when there is a mismatch between data_type and value
        """
        if data_type == cls.DATATYPE.STRING:
            if not isinstance(value, str):
                raise TypeError(f"Value should be string but is {type(value)}.")
            byte_list = value.encode()
            if len(byte_list) % 2:
                byte_list += b"\x00"
        else:
            byte_list = struct.pack(f">{data_type.value[0]}", value)
        regs = [
            int.from_bytes(byte_list[x : x + 2], "big")
            for x in range(0, len(byte_list), 2)
        ]
        return regs
