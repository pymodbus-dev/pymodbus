#!/usr/bin/env python3
"""Modbus Message Generator."""
import argparse
import codecs as c
import logging

import pymodbus.bit_read_message as modbus_bit
import pymodbus.bit_write_message as modbus_bit_write
import pymodbus.diag_message as modbus_diag
import pymodbus.file_message as modbus_file
import pymodbus.mei_message as modbus_mei
import pymodbus.other_message as modbus_other
import pymodbus.register_read_message as modbus_register
import pymodbus.register_write_message as modbus_register_write
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
)


_logger = logging.getLogger()


# -------------------------------------------------------------------------- #
# enumerate all request/response messages
# -------------------------------------------------------------------------- #
messages = [
    (
        modbus_register.ReadHoldingRegistersRequest,
        modbus_register.ReadHoldingRegistersResponse,
    ),
    (modbus_bit.ReadDiscreteInputsRequest, modbus_bit.ReadDiscreteInputsResponse),
    (
        modbus_register.ReadInputRegistersRequest,
        modbus_register.ReadInputRegistersResponse,
    ),
    (modbus_bit.ReadCoilsRequest, modbus_bit.ReadCoilsResponse),
    (
        modbus_bit_write.WriteMultipleCoilsRequest,
        modbus_bit_write.WriteMultipleCoilsResponse,
    ),
    (
        modbus_register_write.WriteMultipleRegistersRequest,
        modbus_register_write.WriteMultipleRegistersResponse,
    ),
    (
        modbus_register_write.WriteSingleRegisterRequest,
        modbus_register_write.WriteSingleRegisterResponse,
    ),
    (modbus_bit_write.WriteSingleCoilRequest, modbus_bit_write.WriteSingleCoilResponse),
    (
        modbus_register.ReadWriteMultipleRegistersRequest,
        modbus_register.ReadWriteMultipleRegistersResponse,
    ),
    (modbus_other.ReadExceptionStatusRequest, modbus_other.ReadExceptionStatusResponse),
    (modbus_other.GetCommEventCounterRequest, modbus_other.GetCommEventCounterResponse),
    (modbus_other.GetCommEventLogRequest, modbus_other.GetCommEventLogResponse),
    (modbus_other.ReportSlaveIdRequest, modbus_other.ReportSlaveIdResponse),
    (modbus_file.ReadFileRecordRequest, modbus_file.ReadFileRecordResponse),
    (modbus_file.WriteFileRecordRequest, modbus_file.WriteFileRecordResponse),
    (
        modbus_register_write.MaskWriteRegisterRequest,
        modbus_register_write.MaskWriteRegisterResponse,
    ),
    (modbus_file.ReadFifoQueueRequest, modbus_file.ReadFifoQueueResponse),
    (modbus_mei.ReadDeviceInformationRequest, modbus_mei.ReadDeviceInformationResponse),
    (modbus_diag.ReturnQueryDataRequest, modbus_diag.ReturnQueryDataResponse),
    (
        modbus_diag.RestartCommunicationsOptionRequest,
        modbus_diag.RestartCommunicationsOptionResponse,
    ),
    (
        modbus_diag.ReturnDiagnosticRegisterRequest,
        modbus_diag.ReturnDiagnosticRegisterResponse,
    ),
    (
        modbus_diag.ChangeAsciiInputDelimiterRequest,
        modbus_diag.ChangeAsciiInputDelimiterResponse,
    ),
    (modbus_diag.ForceListenOnlyModeRequest, modbus_diag.ForceListenOnlyModeResponse),
    (modbus_diag.ClearCountersRequest, modbus_diag.ClearCountersResponse),
    (
        modbus_diag.ReturnBusMessageCountRequest,
        modbus_diag.ReturnBusMessageCountResponse,
    ),
    (
        modbus_diag.ReturnBusCommunicationErrorCountRequest,
        modbus_diag.ReturnBusCommunicationErrorCountResponse,
    ),
    (
        modbus_diag.ReturnBusExceptionErrorCountRequest,
        modbus_diag.ReturnBusExceptionErrorCountResponse,
    ),
    (
        modbus_diag.ReturnSlaveMessageCountRequest,
        modbus_diag.ReturnSlaveMessageCountResponse,
    ),
    (
        modbus_diag.ReturnSlaveNoResponseCountRequest,
        modbus_diag.ReturnSlaveNoResponseCountResponse,
    ),
    (modbus_diag.ReturnSlaveNAKCountRequest, modbus_diag.ReturnSlaveNAKCountResponse),
    (modbus_diag.ReturnSlaveBusyCountRequest, modbus_diag.ReturnSlaveBusyCountResponse),
    (
        modbus_diag.ReturnSlaveBusCharacterOverrunCountRequest,
        modbus_diag.ReturnSlaveBusCharacterOverrunCountResponse,
    ),
    (
        modbus_diag.ReturnIopOverrunCountRequest,
        modbus_diag.ReturnIopOverrunCountResponse,
    ),
    (modbus_diag.ClearOverrunCountRequest, modbus_diag.ClearOverrunCountResponse),
    (modbus_diag.GetClearModbusPlusRequest, modbus_diag.GetClearModbusPlusResponse),
]


def get_commandline(cmdline=None):
    """Parse the command line options."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--framer",
        choices=["ascii", "binary", "rtu", "socket"],
        help="set framer, default is rtu",
        dest="framer",
        default="rtu",
        type=str,
    )
    parser.add_argument(
        "-l",
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help="set log level, default is info",
        dest="log",
        default="info",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="address to use",
        dest="address",
        default=32,
        type=int,
    )
    parser.add_argument(
        "-c",
        "--count",
        help="count to use",
        dest="count",
        default=8,
        type=int,
    )
    parser.add_argument(
        "-v",
        "--value",
        help="value to use",
        dest="value",
        default=1,
        type=int,
    )
    parser.add_argument(
        "-t",
        "--transaction",
        help="transaction to use",
        dest="transaction",
        default=1,
        type=int,
    )
    parser.add_argument(
        "-s",
        "--slave",
        help="slave to use",
        dest="slave",
        default=1,
        type=int,
    )
    args = parser.parse_args(cmdline)
    return args


def generate_messages(cmdline=None):
    """Parse the command line options."""
    args = get_commandline(cmdline=cmdline)
    _logger.setLevel(args.log.upper())

    arguments = {
        "address": args.address,
        "count": args.count,
        "value": args.value,
        "values": [args.value] * args.count,
        "read_address": args.address,
        "read_count": args.count,
        "write_address": args.address,
        "write_registers": [args.value] * args.count,
        "transaction": args.transaction,
        "slave": args.slave,
        "protocol": 0x00,
    }
    framer = {
        "ascii": ModbusAsciiFramer,
        "binary": ModbusBinaryFramer,
        "rtu": ModbusRtuFramer,
        "socket": ModbusSocketFramer,
    }[args.framer](None)

    for entry in messages:
        for inx in (0, 1):
            message = entry[inx](**arguments)
            raw_packet = framer.buildPacket(message)
            packet = c.encode(raw_packet, "hex_codec").decode("utf-8")
            print(f"{message.__class__.__name__:44} = {packet}")
        print("")


if __name__ == "__main__":
    generate_messages()
