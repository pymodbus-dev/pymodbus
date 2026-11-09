"""Configure pytest."""

import pytest

import pymodbus.pdu.data_message as pdu_data
import pymodbus.pdu.diag_message as pdu_diag
import pymodbus.pdu.other_message as pdu_other


@pytest.fixture(
    params=[
        (  # 0
            pdu_data.PDUreadCoils,
            "read_coils",
            (
                {"address": 117, "count": 3},
                b"\x01\x01\x00\x75\x00\x03",
                {"bits": [True, True] + [False] * 6},
                b"\x01\x01\x01\x03",
            ),
        ),
        (  # 1
            pdu_data.PDUwriteSingleCoil,
            "write_coil",
            (
                {"address": 117, "bits": [True]},
                b"\x01\x05\x00\x75\xff\x00",
                {"address": 117, "bits": [True]},
                b"\x01\x05\x00\x75\xff\x00",
            ),
        ),
        (  # 2
            pdu_data.PDUwriteMultipleCoils,
            "write_coils",
            (
                {"address": 117, "bits": [True, False, True]},
                b"\x01\x0f\x00\x75\x00\x03\x01\x05",
                {"address": 117, "count": 3},
                b"\x01\x0f\x00\x75\x00\x03",
            ),
        ),
        (  # 3
            pdu_data.PDUreadDiscreteInputs,
            "read_discrete_inputs",
            (
                {"address": 117, "count": 3},
                b"\x01\x02\x00\x75\x00\x03",
                {"bits": [True, True]},
                b"\x01\x02\x01\x03",
            ),
        ),
        (  # 4
            pdu_data.PDUreadHoldingRegisters,
            "read_holding_registers",
            (
                {"address": 117, "count": 3},
                b"\x01\x03\x00\x75\x00\x03",
                {"registers": [3, 17]},
                b"\x01\x03\x04\x00\x03\x00\x11",
            ),
        ),
        (  # 5
            pdu_data.PDUreadInputRegisters,
            "read_input_registers",
            (
                {"address": 117, "count": 3},
                b"\x01\x04\x00\x75\x00\x03",
                {"registers": [3, 17]},
                b"\x01\x04\x04\x00\x03\x00\x11",
            ),
        ),
        (  # 6
            pdu_data.PDUwriteSingleRegister,
            "write_register",
            (
                {"address": 117, "registers": [112]},
                b"\x01\x06\x00\x75\x00\x70",
                {"address": 117, "registers": [112]},
                b"\x01\x06\x00\x75\x00\x70",
            ),
        ),
        (  # 7
            pdu_data.PDUwriteMultipleRegisters,
            "write_registers",
            (
                {"address": 117, "registers": [111, 121, 131]},
                b"\x01\x10\x00\x75\x00\x03\x06\x00\x6f\x00\x79\x00\x83",
                {"address": 117, "count": 3},
                b"\x01\x10\x00\x75\x00\x03",
            ),
        ),
        (  # 8
            pdu_data.PDUreadWriteMultipleRegisters,
            "readwrite_registers",
            (
                {
                    "address": 17,
                    "count": 2,
                    "write_address": 25,
                    "registers": [111, 112],
                },
                b"\x01\x17\x00\x11\x00\x02\x00\x19\x00\x02\x04\x00\x6f\x00\x70",
                {"registers": [111, 112]},
                b"\x01\x17\x04\x00\x6f\x00\x70",
            ),
        ),
        (  # 9
            pdu_data.PDUmaskWriteRegister,
            "mask_write_register",
            (
                {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234},
                b"\x01\x16\x01\x04\xe1\xd2\x12\x34",
                {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234},
                b"\x01\x16\x01\x04\xe1\xd2\x12\x34",
            ),
        ),
        (  # 10
            pdu_other.PDUreadFileRecord,
            "read_file_record",
            (
                {"records": [pdu_other.FileRecord(), pdu_other.FileRecord()]},
                b"\x01\x14\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00",
                {"records": [pdu_other.FileRecord(), pdu_other.FileRecord()]},
                b"\x01\x14\x04\x01\x06\x01\x06",
            ),
        ),
        (  # 11
            pdu_other.PDUwriteFileRecord,
            "write_file_record",
            (
                {"records": [pdu_other.FileRecord(), pdu_other.FileRecord()]},
                b"\x01\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00",
                {"records": [pdu_other.FileRecord(), pdu_other.FileRecord()]},
                b"\x01\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00",
            ),
        ),
        (  # 12
            pdu_other.PDUreadFifoQueue,
            "read_fifo_queue",
            (
                {"address": 117},
                b"\x01\x18\x00\x75",
                {"values": [123, 456]},
                b"\x01\x18\x00\x06\x00\x02\x00\x7b\x01\xc8",
            ),
        ),
        (  # 13
            pdu_diag.PDUreadDeviceInformation,
            "read_device_information",
            (
                {"read_code": 0x01, "object_id": 0x02},
                b"\x01\x2b\x0e\x01\x02",
                {"read_code": 0x01},
                b"\x01\x2b\x0e\x01\x83\x00\x00\x00",
            ),
        ),
        (  # 14
            pdu_other.PDUreadExceptionStatus,
            "read_exception_status",
            ({}, b"\x01\x07", {"status": 0x23}, b"\x01\x07\x23"),
        ),
        (  # 15
            pdu_other.PDUgetCommEventCounter,
            "diag_get_comm_event_counter",
            ({}, b"\x01\x0b", {"status": 1, "count": 1}, b"\x01\x0b\x00\x00\x00\x01"),
        ),
        (  # 16
            pdu_other.PDUgetCommEventLog,
            "diag_get_comm_event_log",
            (
                {},
                b"\x01\x0c",
                {
                    "status": True,
                    "message_count": 12,
                    "event_count": 7,
                    "events": [12, 14],
                },
                b"\x01\x0c\x08\x00\x00\x00\x07\x00\x0c\x0c\x0e",
            ),
        ),
        (  # 17
            pdu_other.PDUreportDeviceId,
            "report_device_id",
            (
                {},
                b"\x01\x11",
                {"identifier": b"\x12", "status": True},
                b"\x01\x11\x02\x12\xff",
            ),
        ),
        (  # 18
            pdu_diag.PDUreturnQueryData,
            "diag_query_data",
            (
                {},
                b"\x01\x08\x00\x00\x00\x00",
                {},
                b"\x01\x08\x00\x00\x00\x00",
            ),
        ),
        (  # 19
            pdu_diag.PDUreturnQueryData,
            "diag_query_data",
            (
                {"message": b"AB"},
                b"\x01\x08\x00\x00\x41\x42",
                {"message": b"AB"},
                b"\x01\x08\x00\x00\x41\x42",
            ),
        ),
        (  # 20
            pdu_diag.PDUrestartCommunicationsOption,
            "diag_restart_communication",
            (
                {},
                b"\x01\x08\x00\x01\x00\x00",
                {},
                b"\x01\x08\x00\x01\x00\x00",
            ),
        ),
        (  # 21
            pdu_diag.PDUrestartCommunicationsOption,
            "diag_restart_communication",
            (
                {"message": b"\xff\x00"},
                b"\x01\x08\x00\x01\xff\x00",
                {"message": b"\xff\x00"},
                b"\x01\x08\x00\x01\xff\x00",
            ),
        ),
        (  # 22
            pdu_diag.PDUrestartCommunicationsOption,
            "diag_restart_communication",
            (
                {"message": b"\x00\x00"},
                b"\x01\x08\x00\x01\x00\x00",
                {"message": b"\x00\x00"},
                b"\x01\x08\x00\x01\x00\x00",
            ),
        ),
        (  # 23
            pdu_diag.PDUreturnDiagnosticRegister,
            "diag_read_diagnostic_register",
            (
                {},
                b"\x01\x08\x00\x02\x00\x00",
                {},
                b"\x01\x08\x00\x02\x00\x00",
            ),
        ),
        (  # 24
            pdu_diag.PDUreturnDiagnosticRegister,
            "diag_read_diagnostic_register",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x02\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x02\x10\x10",
            ),
        ),
        (  # 25
            pdu_diag.PDUchangeAsciiInputDelimiter,
            "diag_change_ascii_input_delimeter",
            (
                {},
                b"\x01\x08\x00\x03\x00\x00",
                {},
                b"\x01\x08\x00\x03\x00\x00",
            ),
        ),
        (  # 26
            pdu_diag.PDUchangeAsciiInputDelimiter,
            "diag_change_ascii_input_delimeter",
            (
                {"message": b"A\x00"},
                b"\x01\x08\x00\x03\x41\x00",
                {"message": b"A\x00"},
                b"\x01\x08\x00\x03\x41\x00",
            ),
        ),
        (  # 27
            pdu_diag.PDUchangeAsciiInputDelimiter,
            "diag_change_ascii_input_delimeter",
            (
                {"message": b"\n\x00"},
                b"\x01\x08\x00\x03\x0a\x00",
                {"message": b"\n\x00"},
                b"\x01\x08\x00\x03\x0a\x00",
            ),
        ),
        (  # 28
            pdu_diag.PDUforceListenOnlyMode,
            "diag_force_listen_only",
            ({}, b"\x01\x08\x00\x04\x00\x00", {}, b"\x01\x08\x00\x04\x00\x00"),
        ),
        (  # 29
            pdu_diag.PDUforceListenOnlyMode,
            "diag_force_listen_only",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x04\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x04\x10\x10",
            ),
        ),
        (  # 30
            pdu_diag.PDUclearCounters,
            "diag_clear_counters",
            ({}, b"\x01\x08\x00\x0a\x00\x00", {}, b"\x01\x08\x00\n\x00\x00"),
        ),
        (  # 31
            pdu_diag.PDUclearCounters,
            "diag_clear_counters",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0a\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\n\x10\x10",
            ),
        ),
        (  # 32
            pdu_diag.PDUreturnBusMessageCount,
            "diag_read_bus_message_count",
            (
                {},
                b"\x01\x08\x00\x0b\x00\x00",
                {},
                b"\x01\x08\x00\x0b\x00\x00",
            ),
        ),
        (  # 33
            pdu_diag.PDUreturnBusMessageCount,
            "diag_read_bus_message_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0b\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0b\x10\x10",
            ),
        ),
        (  # 34
            pdu_diag.PDUreturnBusCommunicationErrorCount,
            "diag_read_bus_comm_error_count",
            (
                {},
                b"\x01\x08\x00\x0c\x00\x00",
                {},
                b"\x01\x08\x00\x0c\x00\x00",
            ),
        ),
        (  # 35
            pdu_diag.PDUreturnBusCommunicationErrorCount,
            "diag_read_bus_comm_error_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0c\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0c\x10\x10",
            ),
        ),
        (  # 36
            pdu_diag.PDUreturnBusExceptionErrorCount,
            "diag_read_bus_exception_error_count",
            (
                {},
                b"\x01\x08\x00\x0d\x00\x00",
                {},
                b"\x01\x08\x00\x0d\x00\x00",
            ),
        ),
        (  # 37
            pdu_diag.PDUreturnBusExceptionErrorCount,
            "diag_read_bus_exception_error_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0d\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0d\x10\x10",
            ),
        ),
        (  # 38
            pdu_diag.PDUreturnDeviceMessageCount,
            "diag_read_device_message_count",
            (
                {},
                b"\x01\x08\x00\x0e\x00\x00",
                {},
                b"\x01\x08\x00\x0e\x00\x00",
            ),
        ),
        (  # 39
            pdu_diag.PDUreturnDeviceMessageCount,
            "diag_read_device_message_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0e\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0e\x10\x10",
            ),
        ),
        (  # 40
            pdu_diag.PDUreturnDeviceNoResponseCount,
            "diag_read_device_no_response_count",
            (
                {},
                b"\x01\x08\x00\x0f\x00\x00",
                {},
                b"\x01\x08\x00\x0f\x00\x00",
            ),
        ),
        (  # 41
            pdu_diag.PDUreturnDeviceNoResponseCount,
            "diag_read_device_no_response_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0f\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x0f\x10\x10",
            ),
        ),
        (  # 42
            pdu_diag.PDUreturnDeviceNAKCount,
            "diag_read_device_nak_count",
            (
                {},
                b"\x01\x08\x00\x10\x00\x00",
                {},
                b"\x01\x08\x00\x10\x00\x00",
            ),
        ),
        (  # 43
            pdu_diag.PDUreturnDeviceNAKCount,
            "diag_read_device_nak_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x10\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x10\x10\x10",
            ),
        ),
        (  # 44
            pdu_diag.PDUreturnDeviceBusyCount,
            "diag_read_device_busy_count",
            (
                {},
                b"\x01\x08\x00\x11\x00\x00",
                {},
                b"\x01\x08\x00\x11\x00\x00",
            ),
        ),
        (  # 45
            pdu_diag.PDUreturnDeviceBusyCount,
            "diag_read_device_busy_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x11\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x11\x10\x10",
            ),
        ),
        (  # 46
            pdu_diag.PDUreturnDeviceBusCharacterOverrunCount,
            "diag_read_bus_char_overrun_count",
            (
                {},
                b"\x01\x08\x00\x12\x00\x00",
                {},
                b"\x01\x08\x00\x12\x00\x00",
            ),
        ),
        (  # 47
            pdu_diag.PDUreturnDeviceBusCharacterOverrunCount,
            "diag_read_bus_char_overrun_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x12\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x12\x10\x10",
            ),
        ),
        (  # 48
            pdu_diag.PDUreturnIopOverrunCount,
            "diag_read_iop_overrun_count",
            (
                {},
                b"\x01\x08\x00\x13\x00\x00",
                {},
                b"\x01\x08\x00\x13\x00\x00",
            ),
        ),
        (  # 49
            pdu_diag.PDUreturnIopOverrunCount,
            "diag_read_iop_overrun_count",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x13\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x13\x10\x10",
            ),
        ),
        (  # 50
            pdu_diag.PDUclearOverrunCount,
            "diag_clear_overrun_counter",
            (
                {},
                b"\x01\x08\x00\x14\x00\x00",
                {},
                b"\x01\x08\x00\x14\x00\x00",
            ),
        ),
        (  # 51
            pdu_diag.PDUclearOverrunCount,
            "diag_clear_overrun_counter",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x14\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x14\x10\x10",
            ),
        ),
        (  # 52
            pdu_diag.PDUgetClearModbusPlus,
            "diag_getclear_modbus_response",
            (
                {},
                b"\x01\x08\x00\x15\x00\x00",
                {},
                b"\x01\x08\x00\x15\x00\x00",
            ),
        ),
        (  # 53
            pdu_diag.PDUgetClearModbusPlus,
            "diag_getclear_modbus_response",
            (
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x15\x10\x10",
                {"message": b"\x10\x10"},
                b"\x01\x08\x00\x15\x10\x10",
            ),
        ),
    ],
)
def paramPDU(request):
    """Define all requests/responses for use in general tests."""
    pdu, api, entry = request.param
    return pdu, api, entry[0], entry[1], entry[2], entry[3]
