"""
Modbus Clients to be used with REPL.

Copyright (c) 2018 Riptide IO, Inc. All Rights Reserved.

"""
from __future__ import absolute_import, unicode_literals
import functools
from pymodbus.pdu import ModbusExceptions, ExceptionResponse
from pymodbus.exceptions import ModbusIOException
from pymodbus.client.sync import ModbusSerialClient as _ModbusSerialClient
from pymodbus.client.sync import ModbusTcpClient as _ModbusTcpClient
from pymodbus.mei_message import ReadDeviceInformationRequest
from pymodbus.other_message import (ReadExceptionStatusRequest,
                                    ReportSlaveIdRequest,
                                    GetCommEventCounterRequest,
                                    GetCommEventLogRequest)
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
                                   GetClearModbusPlusRequest)


def make_response_dict(resp):
    rd = {
        'function_code': resp.function_code,
        'address': resp.address
    }
    if hasattr(resp, "value"):
        rd['value'] = resp.value
    elif hasattr(resp, 'values'):
        rd['values'] = resp.values
    elif hasattr(resp, 'count'):
        rd['count'] = resp.count

    return rd


def handle_brodcast(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        self = args[0]
        resp = func(*args, **kwargs)
        if kwargs.get("unit") == 0 and self.broadcast_enable:
            return {
                'broadcasted': True
            }
        if not resp.isError():
            return make_response_dict(resp)
        else:
            return ExtendedRequestSupport._process_exception(resp, **kwargs)
    return _wrapper


class ExtendedRequestSupport(object):

    @staticmethod
    def _process_exception(resp, **kwargs):
        unit = kwargs.get("unit")
        if unit == 0:
            err = {
                "message": "Broadcast message, ignoring errors!!!"
            }
        else:
            if isinstance(resp, ExceptionResponse):
                err = {
                    'original_function_code': "{} ({})".format(
                        resp.original_code, hex(resp.original_code)),
                    'error_function_code': "{} ({})".format(
                        resp.function_code, hex(resp.function_code)),
                    'exception code': resp.exception_code,
                    'message': ModbusExceptions.decode(resp.exception_code)
                }
            elif isinstance(resp, ModbusIOException):
                err = {
                    'original_function_code': "{} ({})".format(
                        resp.fcode, hex(resp.fcode)),
                    'error': resp.message
                }
            else:
                err = {
                    'error': str(resp)
                }
        return err

    def read_coils(self, address, count=1, **kwargs):
        """
        Reads `count` coils from a given slave starting at `address`.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :returns: List of register values
        """
        resp = super(ExtendedRequestSupport, self).read_coils(address,
                                                              count, **kwargs)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'bits': resp.bits
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def read_discrete_inputs(self, address, count=1, **kwargs):
        """
        Reads `count` number of discrete inputs starting at offset `address`.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :return: List of bits
        """
        resp = super(ExtendedRequestSupport,
                     self).read_discrete_inputs(address, count, **kwargs)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'bits': resp.bits
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    @handle_brodcast
    def write_coil(self, address, value, **kwargs):
        """
        Write `value` to coil at `address`.

        :param address: coil offset to write to
        :param value: bit value to write
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).write_coil(
            address, value, **kwargs)
        return resp

    @handle_brodcast
    def write_coils(self, address, values, **kwargs):
        """
        Write `value` to coil at `address`.

        :param address: coil offset to write to
        :param values: list of bit values to write (comma seperated)
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).write_coils(
            address, values, **kwargs)
        return resp

    @handle_brodcast
    def write_register(self, address, value, **kwargs):
        """
        Write `value` to register at `address`.

        :param address: register offset to write to
        :param value: register value to write
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).write_register(
            address, value, **kwargs)
        return resp

    @handle_brodcast
    def write_registers(self, address, values, **kwargs):
        """
        Write list of `values` to registers starting at `address`.

        :param address: register offset to write to
        :param values: list of register value to write (comma seperated)
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).write_registers(
            address, values, **kwargs)
        return resp

    def read_holding_registers(self, address, count=1, **kwargs):
        """
        Read `count` number of holding registers starting at `address`.

        :param address: starting register offset to read from
        :param count: Number of registers to read
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).read_holding_registers(
            address, count, **kwargs)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'registers': resp.registers
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def read_input_registers(self, address, count=1, **kwargs):
        """
        Read `count` number of input registers starting at `address`.

        :param address: starting register offset to read from to
        :param count: Number of registers to read
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).read_input_registers(
            address, count, **kwargs)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'registers': resp.registers
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def readwrite_registers(self, read_address, read_count, write_address,
                            write_registers, **kwargs):
        """
        Read `read_count` number of holding registers starting at \
        `read_address`  and write `write_registers` \
        starting at `write_address`.

        :param read_address: register offset to read from
        :param read_count: Number of registers to read
        :param write_address: register offset to write to
        :param write_registers: List of register values to write (comma seperated)
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).readwrite_registers(
            read_address=read_address,
            read_count=read_count,
            write_address=write_address,
            write_registers=write_registers,
            **kwargs
        )
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'registers': resp.registers
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def mask_write_register(self, address=0x0000,
                            and_mask=0xffff, or_mask=0x0000, **kwargs):
        """
        Mask content of holding register at `address`  \
        with `and_mask` and `or_mask`.

        :param address: Reference address of register
        :param and_mask: And Mask
        :param or_mask: OR Mask
        :param unit: The slave unit this request is targeting
        :return:
        """
        resp = super(ExtendedRequestSupport, self).read_input_registers(
            address=address, and_mask=and_mask, or_mask=or_mask, **kwargs)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'address': resp.address,
                'and mask': resp.and_mask,
                'or mask': resp.or_mask
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def read_device_information(self, read_code=None,
                                        object_id=0x00, **kwargs):
        """
        Read the identification and additional information of remote slave.

        :param read_code:  Read Device ID code (0x01/0x02/0x03/0x04)
        :param object_id: Identification of the first object to obtain.
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReadDeviceInformationRequest(read_code, object_id, **kwargs)
        resp = self.execute(request)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'information': resp.information,
                'object count': resp.number_of_objects,
                'conformity': resp.conformity,
                'next object id': resp.next_object_id,
                'more follows': resp.more_follows,
                'space left': resp.space_left
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def report_slave_id(self, **kwargs):
        """
        Report information about remote slave ID.

        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReportSlaveIdRequest(**kwargs)
        resp = self.execute(request)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'identifier': resp.identifier.decode('cp1252'),
                'status': resp.status,
                'byte count': resp.byte_count
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def read_exception_status(self, **kwargs):
        """
         Read the contents of eight Exception Status outputs in a remote \
         device.

        :param unit: The slave unit this request is targeting
        
        :return:

        """
        request = ReadExceptionStatusRequest(**kwargs)
        resp = self.execute(request)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'status': resp.status
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def get_com_event_counter(self, **kwargs):
        """
        Read  status word and an event count from the remote device's \
        communication event counter.

        :param unit: The slave unit this request is targeting

        :return:

        """
        request = GetCommEventCounterRequest(**kwargs)
        resp = self.execute(request)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'status': resp.status,
                'count': resp.count
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def get_com_event_log(self, **kwargs):
        """
        Read  status word, event count, message count, and a field of event
        bytes from the remote device.

        :param unit: The slave unit this request is targeting
        :return:
        """
        request = GetCommEventLogRequest(**kwargs)
        resp = self.execute(request)
        if not resp.isError():
            return {
                'function_code': resp.function_code,
                'status': resp.status,
                'message count': resp.message_count,
                'event count': resp.event_count,
                'events': resp.events,
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def _execute_diagnostic_request(self, request):
        resp = self.execute(request)
        if not resp.isError():
            return {
                'function code': resp.function_code,
                'sub function code': resp.sub_function_code,
                'message': resp.message
            }
        else:
            return ExtendedRequestSupport._process_exception(resp)

    def return_query_data(self, message=0, **kwargs):
        """
        Diagnostic sub command , Loop back data sent in response.

        :param message: Message to be looped back
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnQueryDataRequest(message, **kwargs)
        return self._execute_diagnostic_request(request)

    def restart_comm_option(self, toggle=False, **kwargs):
        """
        Diagnostic sub command, initialize and restart remote devices serial \
        interface and clear all of its communications event counters .

        :param toggle: Toggle Status [ON(0xff00)/OFF(0x0000]
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = RestartCommunicationsOptionRequest(toggle, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_diagnostic_register(self, data=0, **kwargs):
        """
        Diagnostic sub command, Read 16-bit diagnostic register.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnDiagnosticRegisterRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def change_ascii_input_delimiter(self, data=0, **kwargs):
        """
        Diagnostic sub command, Change message delimiter for future requests.

        :param data: New delimiter character
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ChangeAsciiInputDelimiterRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def force_listen_only_mode(self, data=0, **kwargs):
        """
        Diagnostic sub command, Forces the addressed remote device to \
        its Listen Only Mode.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ForceListenOnlyModeRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def clear_counters(self, data=0, **kwargs):
        """
        Diagnostic sub command, Clear all counters and diag registers.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ClearCountersRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_bus_message_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of message detected on bus \
         by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnBusMessageCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_bus_com_error_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of CRC errors \
        received by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnBusCommunicationErrorCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_bus_exception_error_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of Modbus exceptions \
        returned by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnBusExceptionErrorCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_message_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of messages addressed to \
        remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveMessageCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_no_response_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of No responses  by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveNoResponseCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_no_ack_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of NO ACK exceptions sent \
         by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveNAKCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_busy_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of server busy exceptions sent \
         by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveBusyCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_slave_bus_char_overrun_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of messages not handled \
         by remote slave due to character overrun condition.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnSlaveBusCharacterOverrunCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def return_iop_overrun_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Return count of iop overrun errors \
        by remote slave.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ReturnIopOverrunCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def clear_overrun_count(self, data=0, **kwargs):
        """
        Diagnostic sub command, Clear over run counter.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = ClearOverrunCountRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)

    def get_clear_modbus_plus(self, data=0, **kwargs):
        """
        Diagnostic sub command, Get or clear stats of remote \
         modbus plus device.

        :param data: Data field (0x0000)
        :param unit: The slave unit this request is targeting
        :return:
        """
        request = GetClearModbusPlusRequest(data, **kwargs)
        return self._execute_diagnostic_request(request)


class ModbusSerialClient(ExtendedRequestSupport, _ModbusSerialClient):
    def __init__(self, method, **kwargs):
        super(ModbusSerialClient, self).__init__(method, **kwargs)

    def get_port(self):
        """
        Serial Port.

        :return: Current Serial port
        """
        return self.port

    def set_port(self, value):
        """
        Serial Port setter.

        :param value: New port
        """
        self.port = value
        if self.is_socket_open():
            self.close()

    def get_stopbits(self):
        """
        Number of stop bits.

        :return: Current Stop bits
        """
        return self.stopbits

    def set_stopbits(self, value):
        """
        Stop bit setter.

        :param value: Possible values (1, 1.5, 2)
        """
        self.stopbits = float(value)
        if self.is_socket_open():
            self.close()

    def get_bytesize(self):
        """
        Number of data bits.

        :return: Current bytesize
        """
        return self.bytesize

    def set_bytesize(self, value):
        """
        Byte size setter.

        :param value: Possible values (5, 6, 7, 8)

        """
        self.bytesize = int(value)
        if self.is_socket_open():
            self.close()

    def get_parity(self):
        """
        Enable Parity Checking.

        :return: Current parity setting
        """
        return self.parity

    def set_parity(self, value):
        """
        Parity Setter.

        :param value: Possible values ('N', 'E', 'O', 'M', 'S')
        """
        self.parity = value
        if self.is_socket_open():
            self.close()

    def get_baudrate(self):
        """
        Serial Port baudrate.

        :return: Current baudrate
        """
        return self.baudrate

    def set_baudrate(self, value):
        """
        Baudrate setter.

        :param value: <supported baudrate>
        """
        self.baudrate = int(value)
        if self.is_socket_open():
            self.close()

    def get_timeout(self):
        """
        Serial Port Read timeout.

        :return: Current read imeout.
        """
        return self.timeout

    def set_timeout(self, value):
        """
        Read timeout setter.

        :param value: Read Timeout in seconds
        """
        self.timeout = float(value)
        if self.is_socket_open():
            self.close()

    def get_serial_settings(self):
        """
        Gets Current Serial port settings.

        :return: Current Serial settings as dict.
        """
        return {
            'baudrate': self.baudrate,
            'port': self.port,
            'parity': self.parity,
            'stopbits': self.stopbits,
            'bytesize': self.bytesize,
            'read timeout': self.timeout,
            't1.5': self.inter_char_timeout,
            't3.5': self.silent_interval
        }


class ModbusTcpClient(ExtendedRequestSupport, _ModbusTcpClient):
    def __init__(self, **kwargs):
        super(ModbusTcpClient, self).__init__(**kwargs)
