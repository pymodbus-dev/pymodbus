"""Modbus Clients to be used with REPL.

Copyright (c) 2018 Riptide IO, Inc. All Rights Reserved.

"""
import functools
from pymodbus.pdu import ModbusExceptions, ExceptionResponse
from pymodbus.exceptions import ModbusIOException
from pymodbus.client.sync import ModbusSerialClient as _ModbusSerialClient
from pymodbus.client.sync import ModbusTcpClient as _ModbusTcpClient
from pymodbus.mei_message import ReadDeviceInformationRequest
from pymodbus.other_message import (
    ReadExceptionStatusRequest,
    ReportSlaveIdRequest,
    GetCommEventCounterRequest,
    GetCommEventLogRequest,
)
from pymodbus.diag_message import (
    ReturnQueryDataRequest,
    RestartCommunicationsOptionRequest,
    ReturnDiagnosticRegisterRequest,
    ChangeAsciiInputDelimiterRequest,
    ForceListenOnlyModeRequest,
    ClearCountersRequest,
    ReturnBusMessageCountRequest,
    ReturnBusCommunicationErrorCountRequest,
    ReturnBusExceptionErrorCountRequest,
    ReturnSlaveMessageCountRequest,
    ReturnSlaveNoResponseCountRequest,
    ReturnSlaveNAKCountRequest,
    ReturnSlaveBusyCountRequest,
    ReturnSlaveBusCharacterOverrunCountRequest,
    ReturnIopOverrunCountRequest,
    ClearOverrunCountRequest,
    GetClearModbusPlusRequest,
)


def make_response_dict(resp):
    """Make response dict."""
    resp_dict = {"function_code": resp.function_code, "address": resp.address}
    if hasattr(resp, "value"):
        resp_dict["value"] = resp.value
    elif hasattr(resp, "values"):
        resp_dict["values"] = resp.values
    elif hasattr(resp, "count"):
        resp_dict["count"] = resp.count
    return resp_dict


def handle_brodcast(func):
    """Handle broadcast."""

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        self = args[0]
        resp = func(*args, **kwargs)
        if not kwargs.get("unit") and self.broadcast_enable:
            return {"broadcasted": True}
        if not resp.isError():
            return make_response_dict(resp)
        return ExtendedRequestSupport._process_exception(  # pylint: disable=protected-access
            resp, **kwargs
        )

    return _wrapper


class ExtendedRequestSupport:  # pylint: disable=(too-many-public-methods
    """Extended request support."""

    @staticmethod
    def _process_exception(resp, **kwargs):
        """Process exception."""
        if not kwargs.get("unit"):
            err = {"message": "Broadcast message, ignoring errors!!!"}
        elif isinstance(resp, ExceptionResponse):
            err = {
                "original_function_code": f"{resp.original_code} ({hex(resp.original_code)})",
                "error_function_code": f"{resp.function_code} ({hex(resp.function_code)})",
                "exception code": resp.exception_code,
                "message": ModbusExceptions.decode(resp.exception_code),
            }
        elif isinstance(resp, ModbusIOException):
            err = {
                "original_function_code": f"{resp.fcode} ({hex(resp.fcode)})",
                "error": resp.message,
            }
        else:
            err = {"error": str(resp)}
        return err

    def read_coils(self, address, count=1, **kwargs):
        """Read `count` coils from a given slave starting at `address`.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :returns: List of register values
        """
        resp = super().read_coils(address, count, **kwargs)  # pylint: disable=no-member
        if not resp.isError():
            return {"function_code": resp.function_code, "bits": resp.bits}
        return ExtendedRequestSupport._process_exception(resp)

    def read_discrete_inputs(self, address, count=1, **kwargs):
        """Read `count` number of discrete inputs starting at offset `address`.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :return: List of bits
        """
        resp = super().read_discrete_inputs(  # pylint: disable=no-member
            address, count, **kwargs
        )
        if not resp.isError():
            return {"function_code": resp.function_code, "bits": resp.bits}
        return ExtendedRequestSupport._process_exception(resp)

    @handle_brodcast
    def write_coil(self, address, value, **kwargs):
        """Write `value` to coil at `address`.

        :param address: coil offset to write to
        :param value: bit value to write
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().write_coil(address, value, **kwargs)  # pylint: disable=no-member
        return resp

    @handle_brodcast
    def write_coils(self, address, values, **kwargs):
        """Write `value` to coil at `address`.

        :param address: coil offset to write to
        :param values: list of bit values to write (comma separated)
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().write_coils(  # pylint: disable=no-member
            address, values, **kwargs
        )
        return resp

    @handle_brodcast
    def write_register(self, address, value, **kwargs):
        """Write `value` to register at `address`.

        :param address: register offset to write to
        :param value: register value to write
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().write_register(  # pylint: disable=no-member
            address, value, **kwargs
        )
        return resp

    @handle_brodcast
    def write_registers(self, address, values, **kwargs):
        """Write list of `values` to registers starting at `address`.

        :param address: register offset to write to
        :param values: list of register value to write (comma separated)
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().write_registers(  # pylint: disable=no-member
            address, values, **kwargs
        )
        return resp

    def read_holding_registers(self, address, count=1, **kwargs):
        """Read `count` number of holding registers starting at `address`.

        :param address: starting register offset to read from
        :param count: Number of registers to read
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().read_holding_registers(  # pylint: disable=no-member
            address, count, **kwargs
        )
        if not resp.isError():
            return {"function_code": resp.function_code, "registers": resp.registers}
        return ExtendedRequestSupport._process_exception(resp)

    def read_input_registers(self, address, count=1, **kwargs):
        """Read `count` number of input registers starting at `address`.

        :param address: starting register offset to read from to
        :param count: Number of registers to read
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().read_input_registers(  # pylint: disable=no-member
            address, count, **kwargs
        )
        if not resp.isError():
            return {"function_code": resp.function_code, "registers": resp.registers}
        return ExtendedRequestSupport._process_exception(resp)

    def readwrite_registers(
        self, read_address, read_count, write_address, write_registers, **kwargs
    ):
        """Read `read_count` number of holding registers.

        Starting at `read_address`
        and write `write_registers` starting at `write_address`.

        :param read_address: register offset to read from
        :param read_count: Number of registers to read
        :param write_address: register offset to write to
        :param write_registers: List of register values to write (comma separated)
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().readwrite_registers(  # pylint: disable=no-member
            read_address=read_address,
            read_count=read_count,
            write_address=write_address,
            write_registers=write_registers,
            **kwargs,
        )
        if not resp.isError():
            return {"function_code": resp.function_code, "registers": resp.registers}
        return ExtendedRequestSupport._process_exception(resp)

    def mask_write_register(
        self, address=0x0000, and_mask=0xFFFF, or_mask=0x0000, **kwargs
    ):
        """Mask content of holding register at `address` with `and_mask` and `or_mask`.

        :param address: Reference address of register
        :param and_mask: And Mask
        :param or_mask: OR Mask
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super().mask_write_register(  # pylint: disable=no-member
            address=address, and_mask=and_mask, or_mask=or_mask, **kwargs
        )
        if not resp.isError():
            return {
                "function_code": resp.function_code,
                "address": resp.address,
                "and mask": resp.and_mask,
                "or mask": resp.or_mask,
            }
        return ExtendedRequestSupport._process_exception(resp)

    def read_device_information(self, read_code=None, object_id=0x00, **kwargs):
        """Read the identification and additional information of remote slave.

        :param read_code:  Read Device ID code (0x01/0x02/0x03/0x04)
        :param object_id: Identification of the first object to obtain.
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReadDeviceInformationRequest(read_code, object_id, **kwargs)
        resp = self.execute(request)  # pylint: disable=no-member
        if not resp.isError():
            return {
                "function_code": resp.function_code,
                "information": resp.information,
                "object count": resp.number_of_objects,
                "conformity": resp.conformity,
                "next object id": resp.next_object_id,
                "more follows": resp.more_follows,
                "space left": resp.space_left,
            }
        return ExtendedRequestSupport._process_exception(resp)

    def report_slave_id(self, **kwargs):
        """Report information about remote slave ID.

        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReportSlaveIdRequest(**kwargs)
        resp = self.execute(request)  # pylint: disable=no-member
        if not resp.isError():
            return {
                "function_code": resp.function_code,
                "identifier": resp.identifier.decode("cp1252"),
                "status": resp.status,
                "byte count": resp.byte_count,
            }
        return ExtendedRequestSupport._process_exception(resp)

    def read_exception_status(self, **kwargs):
        """Read tcontents of eight Exception Status output.

        In a remote device.

        :param unit: The slave unit this request is targeting

        :return:

        """
        request = ReadExceptionStatusRequest(**kwargs)
        resp = self.execute(request)  # pylint: disable=no-member
        if not resp.isError():
            return {"function_code": resp.function_code, "status": resp.status}
        return ExtendedRequestSupport._process_exception(resp)

    def get_com_event_counter(self, **kwargs):
        """Read status word and an event count.

        From the remote device"s communication event counter.

        :param unit: The slave unit this request is targeting

        :return:

        """
        request = GetCommEventCounterRequest(**kwargs)
        resp = self.execute(request)  # pylint: disable=no-member
        if not resp.isError():
            return {
                "function_code": resp.function_code,
                "status": resp.status,
                "count": resp.count,
            }
        return ExtendedRequestSupport._process_exception(resp)

    def get_com_event_log(self, **kwargs):
        """Read status word.

        Event count, message count, and a field of event
        bytes from the remote device.

        :param unit: The slave unit this request is targeting
        :return:
        """
        request = GetCommEventLogRequest(**kwargs)
        resp = self.execute(request)  # pylint: disable=no-member
        if not resp.isError():
            return {
                "function_code": resp.function_code,
                "status": resp.status,
                "message count": resp.message_count,
                "event count": resp.event_count,
                "events": resp.events,
            }
        return ExtendedRequestSupport._process_exception(resp)

    def _execute_diagnostic_request(self, request):
        """Execute diagnostic request."""
        resp = self.execute(request)  # pylint: disable=no-member
        if not resp.isError():
            return {
                "function code": resp.function_code,
                "sub function code": resp.sub_function_code,
                "message": resp.message,
            }
        return ExtendedRequestSupport._process_exception(resp)

    def return_query_data(self, message=0, **kwargs):
        """Loop back data sent in response.

        :param message: Message to be looped back
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnQueryDataRequest(message, **kwargs)
        return self._execute_diagnostic_request(request)

    def restart_comm_option(self, toggle=False, **kwargs):
        """Initialize and restart remote devices.

        Serial interface and clear all of its communications event counters.

        :param toggle: Toggle Status [ON(0xff00)/OFF(0x0000]
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = RestartCommunicationsOptionRequest(toggle, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_diagnostic_register(self, data=0, **kwargs):
        """Read 16-bit diagnostic register.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnDiagnosticRegisterRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def change_ascii_input_delimiter(self, data=0, **kwargs):
        """Change message delimiter for future requests.

        :param data: New delimiter character
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ChangeAsciiInputDelimiterRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def force_listen_only_mode(self, data=0, **kwargs):
        """Force addressed remote device to its Listen Only Mode.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ForceListenOnlyModeRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def clear_counters(self, data=0, **kwargs):
        """Clear all counters and diag registers.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ClearCountersRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_bus_message_count(self, data=0, **kwargs):
        """Return count of message detected on bus by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnBusMessageCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_bus_com_error_count(self, data=0, **kwargs):
        """Return count of CRC errors received by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnBusCommunicationErrorCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_bus_exception_error_count(self, data=0, **kwargs):
        """Return count of Modbus exceptions returned by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnBusExceptionErrorCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_message_count(self, data=0, **kwargs):
        """Return count of messages addressed to remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveMessageCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_no_response_count(self, data=0, **kwargs):
        """Return count of No responses by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveNoResponseCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_no_ack_count(self, data=0, **kwargs):
        """Return count of NO ACK exceptions sent by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveNAKCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_busy_count(self, data=0, **kwargs):
        """Return count of server busy exceptions sent by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveBusyCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_bus_char_overrun_count(self, data=0, **kwargs):
        """Return count of messages not handled.

        By remote slave due to character overrun condition.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveBusCharacterOverrunCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_iop_overrun_count(self, data=0, **kwargs):
        """Return count of iop overrun errors by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnIopOverrunCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def clear_overrun_count(self, data=0, **kwargs):
        """Clear over run counter.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ClearOverrunCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def get_clear_modbus_plus(self, data=0, **kwargs):
        """Get/clear stats of remote modbus plus device.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = GetClearModbusPlusRequest(  # pylint: disable=too-many-function-args
            data, **kwargs
        )
        return self._execute_diagnostic_request(request)


class ModbusSerialClient(ExtendedRequestSupport, _ModbusSerialClient):
    """Modbus serial client."""

    def __init__(self, method, **kwargs):
        """Initialize."""
        super().__init__(method, **kwargs)

    def get_port(self):
        """Get serial Port.

        :return: Current Serial port
        """
        return self.port

    def set_port(self, value):
        """Set serial Port setter.

        :param value: New port
        """
        self.port = value
        if self.is_socket_open():
            self.close()

    def get_stopbits(self):
        """Get number of stop bits.

        :return: Current Stop bits
        """
        return self.stopbits

    def set_stopbits(self, value):
        """Set stop bit.

        :param value: Possible values (1, 1.5, 2)
        """
        self.stopbits = float(value)
        if self.is_socket_open():
            self.close()

    def get_bytesize(self):
        """Get number of data bits.

        :return: Current bytesize
        """
        return self.bytesize

    def set_bytesize(self, value):
        """Set Byte size.

        :param value: Possible values (5, 6, 7, 8)

        """
        self.bytesize = int(value)
        if self.is_socket_open():
            self.close()

    def get_parity(self):
        """Enable Parity Checking.

        :return: Current parity setting
        """
        return self.parity

    def set_parity(self, value):
        """Set parity Setter.

        :param value: Possible values ("N", "E", "O", "M", "S")
        """
        self.parity = value
        if self.is_socket_open():
            self.close()

    def get_baudrate(self):
        """Get serial Port baudrate.

        :return: Current baudrate
        """
        return self.baudrate

    def set_baudrate(self, value):
        """Set baudrate setter.

        :param value: <supported baudrate>
        """
        self.baudrate = int(value)
        if self.is_socket_open():
            self.close()

    def get_timeout(self):
        """Get serial Port Read timeout.

        :return: Current read imeout.
        """
        return self.timeout

    def set_timeout(self, value):
        """Read timeout setter.

        :param value: Read Timeout in seconds
        """
        self.timeout = float(value)
        if self.is_socket_open():
            self.close()

    def get_serial_settings(self):
        """Get Current Serial port settings.

        :return: Current Serial settings as dict.
        """
        return {
            "baudrate": self.baudrate,
            "port": self.port,
            "parity": self.parity,
            "stopbits": self.stopbits,
            "bytesize": self.bytesize,
            "read timeout": self.timeout,
            "t1.5": self.inter_char_timeout,
            "t3.5": self.silent_interval,
        }


class ModbusTcpClient(ExtendedRequestSupport, _ModbusTcpClient):
    """TCP client."""

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
