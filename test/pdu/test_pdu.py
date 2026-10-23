"""Test pdu."""

from typing import Any

import pytest

import pymodbus.pdu.bit_message as bit_msg
import pymodbus.pdu.diag_message as pdu_diag
import pymodbus.pdu.file_message as file_msg
import pymodbus.pdu.mei_message as mei_msg
import pymodbus.pdu.other_message as o_msg
import pymodbus.pdu.register_message as reg_msg
from pymodbus.constants import ModbusStatus
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import (
    DecodePDU,
    ModbusControlBlock,
    OLD_pdu,
    PDUexception,
)
from pymodbus.pdu.utils import pack_bitstring, unpack_bitstring


class TestPdu:
    """Test modbus PDU."""

    exception = PDUexception(1, 1, 0)

    async def test_error_methods(self):
        """Test all error methods."""
        result = self.exception.x_encode()
        assert result == b"\x01"
        DecodePDU(True).decode(b"\x81" + result)
        assert self.exception.exception_code == 1
        self.exception.x_decode(b"")

    async def test_pdu_id(self, mockPDU):
        """Test set illegal pdu id."""
        with pytest.raises(ModbusIOException) as exc_info:
            mockPDU(256, transaction_id=0x42)
        assert exc_info.value.dev_id == 256
        assert exc_info.value.transaction_id == 0x42

    async def test_is_error(self):
        """Test is_error."""
        assert self.exception.isError()

    requests: list[tuple[type[OLD_pdu], tuple[Any, ...], dict[str, Any], bytes]] = [
        (
            bit_msg.PDUreadCoils,
            (0,),
            {"address": 117, "count": 3},
            b"\x01\x00\x75\x00\x03",
        ),
        (
            bit_msg.PDUreadDiscreteInputs,
            (0,),
            {"address": 117, "count": 3},
            b"\x02\x00\x75\x00\x03",
        ),
        (
            bit_msg.PDUwriteSingleCoil,
            (0,),
            {"address": 117, "bits": [True]},
            b"\x05\x00\x75\xff\x00",
        ),
        (
            bit_msg.PDUwriteMultipleCoils,
            (0,),
            {"address": 117, "bits": [True, False, True]},
            b"\x0f\x00\x75\x00\x03\x01\x05",
        ),
        (pdu_diag.PDUdiagnostic, (), {"message": None}, b"\x08\x27\x0f"),
        (pdu_diag.PDUdiagnostic, (), {"message": 0x1010}, b"\x08\x27\x0f\x10\x10"),
        (
            pdu_diag.PDUreturnQueryData,
            (),
            {"message": b"\x10\x01"},
            b"\x08\x00\x00\x10\x01",
        ),
        (
            pdu_diag.PDUrestartCommunicationsOption,
            (),
            {"message": ModbusStatus.ON},
            b"\x08\x00\x01\xff\x00",
        ),
        (
            pdu_diag.PDUreturnDiagnosticRegister,
            (),
            {"message": 0x1010},
            b"\x08\x00\x02\x10\x10",
        ),
        (
            pdu_diag.PDUchangeAsciiInputDelimiter,
            (),
            {"message": 0x1010},
            b"\x08\x00\x03\x10\x10",
        ),
        (pdu_diag.PDUforceListenOnlyMode, (), {}, b"\x08\x00\x04\x00\x00"),
        (pdu_diag.PDUclearCounters, (), {"message": 0x1010}, b"\x08\x00\n\x10\x10"),
        (
            pdu_diag.PDUreturnBusMessageCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0b\x10\x10",
        ),
        (
            pdu_diag.PDUreturnBusCommunicationErrorCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0c\x10\x10",
        ),
        (
            pdu_diag.PDUreturnBusExceptionErrorCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0d\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceMessageCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0e\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceNoResponseCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0f\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceNAKCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x10\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceBusyCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x11\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceBusCharacterOverrunCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x12\x10\x10",
        ),
        (
            pdu_diag.PDUreturnIopOverrunCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x13\x10\x10",
        ),
        (
            pdu_diag.PDUclearOverrunCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x14\x10\x10",
        ),
        (
            pdu_diag.PDUgetClearModbusPlus,
            (),
            {"message": 0x1010},
            b"\x08\x00\x15\x10\x10",
        ),
        (
            file_msg.PDUreadFileRecord,
            (),
            {"records": [file_msg.FileRecord(), file_msg.FileRecord()]},
            b"\x14\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00",
        ),
        (
            file_msg.PDUwriteFileRecord,
            (),
            {"records": [file_msg.FileRecord(), file_msg.FileRecord()]},
            b"\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00",
        ),
        (file_msg.PDUreadFifoQueue, (), {"address": 117}, b"\x18\x00\x75"),
        (
            mei_msg.PDUreadDeviceInformation,
            (),
            {"read_code": 0x17, "object_id": 0x29},
            b"\x2b\x0e\x17\x29",
        ),
        (o_msg.PDUreadExceptionStatus, (), {}, b"\x07"),
        (o_msg.PDUgetCommEventCounter, (), {}, b"\x0b"),
        (o_msg.PDUgetCommEventLog, (), {}, b"\x0c"),
        (o_msg.PDUreportDeviceId, (), {}, b"\x11"),
        (
            reg_msg.PDUreadHoldingRegisters,
            (),
            {"address": 117, "count": 3},
            b"\x03\x00\x75\x00\x03",
        ),
        (
            reg_msg.PDUreadInputRegisters,
            (),
            {"address": 117, "count": 3},
            b"\x04\x00\x75\x00\x03",
        ),
        (
            reg_msg.PDUreadWriteMultipleRegisters,
            (),
            {
                "read_address": 17,
                "read_count": 2,
                "write_address": 25,
                "write_registers": [111, 112],
            },
            b"\x17\x00\x11\x00\x02\x00\x19\x00\x02\x04\x00\x6f\x00\x70",
        ),
        (
            reg_msg.PDUwriteMultipleRegisters,
            (),
            {"address": 117, "registers": [111, 121, 131]},
            b"\x10\x00\x75\x00\x03\x06\x00\x6f\x00\x79\x00\x83",
        ),
        (
            reg_msg.PDUwriteSingleRegister,
            (),
            {"address": 117, "registers": [112]},
            b"\x06\x00\x75\x00\x70",
        ),
        (
            reg_msg.PDUmaskWriteRegister,
            (),
            {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234},
            b"\x16\x01\x04\xe1\xd2\x12\x34",
        ),
    ]

    responses: list[tuple[type[OLD_pdu], tuple[Any, ...], dict[str, Any], bytes]] = [
        (
            bit_msg.PDUreadCoils,
            (0,),
            {"bits": [True, True] + [False] * 6, "address": 17, "is_request": False},
            b"\x01\x01\x03",
        ),
        (
            bit_msg.PDUreadDiscreteInputs,
            (0,),
            {"bits": [True, True], "address": 17, "is_request": False},
            b"\x02\x01\x03",
        ),
        (
            bit_msg.PDUwriteSingleCoil,
            (0,),
            {"address": 117, "bits": [True], "is_request": False},
            b"\x05\x00\x75\xff\x00",
        ),
        (
            bit_msg.PDUwriteMultipleCoils,
            (0,),
            {"address": 117, "count": 3, "is_request": False},
            b"\x0f\x00\x75\x00\x03",
        ),
        (pdu_diag.PDUdiagnostic, (), {"message": None}, b"\x08\x27\x0f"),
        (pdu_diag.PDUdiagnostic, (), {"message": 0x1010}, b"\x08\x27\x0f\x10\x10"),
        (
            pdu_diag.PDUreturnQueryData,
            (),
            {"message": b"AB"},
            b"\x08\x00\x00\x41\x42",
        ),
        (
            pdu_diag.PDUrestartCommunicationsOption,
            (),
            {"message": ModbusStatus.ON},
            b"\x08\x00\x01\xff\x00",
        ),
        (
            pdu_diag.PDUreturnDiagnosticRegister,
            (),
            {"message": 0x1010},
            b"\x08\x00\x02\x10\x10",
        ),
        (
            pdu_diag.PDUchangeAsciiInputDelimiter,
            (),
            {"message": 0x1010},
            b"\x08\x00\x03\x10\x10",
        ),
        (pdu_diag.PDUforceListenOnlyMode, (), {}, b"\x08\x00\x04"),
        (
            pdu_diag.PDUclearCounters,
            (),
            {"message": 0x1010},
            b"\x08\x00\n\x10\x10",
        ),
        (
            pdu_diag.PDUreturnBusMessageCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0b\x10\x10",
        ),
        (
            pdu_diag.PDUreturnBusCommunicationErrorCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0c\x10\x10",
        ),
        (
            pdu_diag.PDUreturnBusExceptionErrorCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0d\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceMessageCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0e\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceNoResponseCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x0f\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceNAKCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x10\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceBusyCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x11\x10\x10",
        ),
        (
            pdu_diag.PDUreturnDeviceBusCharacterOverrunCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x12\x10\x10",
        ),
        (
            pdu_diag.PDUreturnIopOverrunCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x13\x10\x10",
        ),
        (
            pdu_diag.PDUclearOverrunCount,
            (),
            {"message": 0x1010},
            b"\x08\x00\x14\x10\x10",
        ),
        (
            pdu_diag.PDUgetClearModbusPlus,
            (),
            {"message": 0x1010},
            b"\x08\x00\x15\x10\x10",
        ),
        (
            file_msg.PDUreadFileRecord,
            (),
            {"records": [file_msg.FileRecord(), file_msg.FileRecord()]},
            b"\x14\x04\x01\x06\x01\x06",
        ),
        (
            file_msg.PDUwriteFileRecord,
            (),
            {"records": [file_msg.FileRecord(), file_msg.FileRecord()]},
            b"\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00",
        ),
        (
            file_msg.PDUreadFifoQueue,
            (),
            {"values": [123, 456]},
            b"\x18\x00\x06\x00\x02\x00{\x01\xc8",
        ),
        (
            mei_msg.PDUreadDeviceInformation,
            (),
            {"read_code": 0x17},
            b"\x2b\x0e\x17\x83\x00\x00\x00",
        ),
        (o_msg.PDUreadExceptionStatus, (), {"status": 0x23}, b"\x07\x23"),
        (
            o_msg.PDUgetCommEventCounter,
            (),
            {"count": 123},
            b"\x0b\x00\x00\x00\x7b",
        ),
        (
            o_msg.PDUgetCommEventLog,
            (),
            {"status": True, "message_count": 12, "event_count": 7, "events": [12, 14]},
            b"\x0c\x08\x00\x00\x00\x07\x00\x0c\x0c\x0e",
        ),
        (
            o_msg.PDUreportDeviceId,
            (),
            {"identifier": b"\x12", "status": True},
            b"\x11\x02\x12\xff",
        ),
        (
            reg_msg.PDUreadHoldingRegisters,
            (),
            {"registers": [3, 17]},
            b"\x03\x04\x00\x03\x00\x11",
        ),
        (
            reg_msg.PDUreadInputRegisters,
            (),
            {"registers": [3, 17]},
            b"\x04\x04\x00\x03\x00\x11",
        ),
        (
            reg_msg.PDUreadWriteMultipleRegisters,
            (),
            {"registers": [1, 2]},
            b"\x17\x04\x00\x01\x00\x02",
        ),
        (
            reg_msg.PDUwriteSingleRegister,
            (),
            {"address": 117, "registers": [112]},
            b"\x06\x00\x75\x00\x70",
        ),
        (
            reg_msg.PDUwriteMultipleRegisters,
            (),
            {"address": 117, "count": 3},
            b"\x10\x00\x75\x00\x03",
        ),
        (
            reg_msg.PDUmaskWriteRegister,
            (),
            {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234},
            b"\x16\x01\x04\xe1\xd2\x12\x34",
        ),
    ]

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests)
    @pytest.mark.usefixtures("kwargs", "args", "frame")
    def test_pdu_instance(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        assert pdu

    @pytest.mark.parametrize(
        ("pdutype", "args", "kwargs", "frame"), requests + responses
    )
    @pytest.mark.usefixtures("frame", "args")
    def test_pdu_instance_args(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        assert pdu
        assert pdutype.__name__ in str(pdu)

    @pytest.mark.parametrize(
        ("pdutype", "args", "kwargs", "frame"), requests + responses
    )
    @pytest.mark.usefixtures("frame", "args")
    def test_pdu_instance_extras(self, pdutype, kwargs):
        """Test that all PDU types can be created."""
        tid = 9112
        dev_id = 63
        pdu = pdutype(transaction_id=tid, dev_id=dev_id, **kwargs)
        assert pdu
        assert str(pdu)
        assert pdu.dev_id == dev_id
        assert pdu.transaction_id == tid
        assert pdu.function_code > 0

    def test_pdu_register_as_byte(self):
        """Test verify functions."""
        registers = [int.from_bytes(b"ab", "big"), int.from_bytes(b"cd", "big")]
        # NOT ALLOWED, NO conversion.
        req = reg_msg.PDUreadHoldingRegisters(address=117, registers=registers, count=3)
        assert len(req.registers) == 2
        assert req.registers[0] == 24930
        assert req.registers[1] == 25444

    def test_pdu_verify_address(self):
        """Test verify functions."""
        req = reg_msg.PDUreadHoldingRegisters(address=10, count=3)
        req.address = -1
        with pytest.raises(ValueError):  # noqa: PT011
            req.verifyAddress()
        req.address = 66000
        with pytest.raises(ValueError):  # noqa: PT011
            req.verifyAddress()

    def test_pdu_verify_count(self):
        """Test verify functions."""
        req = reg_msg.PDUreadHoldingRegisters(address=2, count=0)
        req.count = 0
        with pytest.raises(ValueError):  # noqa: PT011
            req.verifyCount(100)
        req.count = 101
        with pytest.raises(ValueError):  # noqa: PT011
            req.verifyCount(100)
        with pytest.raises(ValueError):  # noqa: PT011
            req.verifyCount(100, count=0)

    @pytest.mark.parametrize(
        ("pdutype", "args", "kwargs", "frame"), requests + responses
    )
    @pytest.mark.usefixtures("args")
    def test_pdu_instance_encode(self, pdutype, args, kwargs, frame):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        res_frame = pdutype.function_code.to_bytes(1, "big") + pdu.x_encode()
        assert res_frame == frame

    @pytest.mark.parametrize(
        ("pdutype", "args", "kwargs", "frame"), requests + responses
    )
    @pytest.mark.usefixtures("args")
    def test_pdu_decode(self, pdutype, args, kwargs, frame):
        """Test pdu decode."""
        pdu = pdutype(*args, **kwargs)
        pdu.x_decode(frame[1:])

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests)
    @pytest.mark.usefixtures("frame", "args")
    async def test_pdu_datastore(self, pdutype, args, kwargs, mock_server_context):
        """Test that all PDU types can be created."""
        control = ModbusControlBlock()
        try:
            pdu = pdutype(*args, **kwargs)
            assert await pdu.datastore_update(mock_server_context(), 1)
        finally:
            control.Delimiter = b"\n"

    @pytest.mark.parametrize(
        ("bytestream", "bitlist"),
        [
            (b"\x01\x00", [True] + [False] * 15),
            (b"\x00\x80", [False] * 15 + [True]),
            (b"\x00\x01", [False] * 8 + [True] + [False] * 7),
            (b"\x01\x80", [True] + [False] * 14 + [True]),
            (b"\x00\x05", [False] * 8 + [True, False, True] + [False] * 5),
            (b"\x01\x05", [True] + [False] * 7 + [True, False, True] + [False] * 5),
            (
                b"\x81\x05",
                [True] + [False] * 6 + [True, True, False, True] + [False] * 5,
            ),
            (
                b"\x00\x01\x81\x05",
                [False] * 8
                + [True]
                + [False] * 7
                + [True]
                + [False] * 6
                + [True, True, False, True]
                + [False] * 5,
            ),
            (b"\x01\x00", [True]),
            (b"\x00\x01", [False] * 8 + [True]),
            (b"\x00\x05", [False] * 8 + [True, False, True]),
            (b"\x01\x05", [True] + [False] * 7 + [True, False, True]),
            (b"\x81\x05", [True] + [False] * 6 + [True, True, False, True]),
            (
                b"\x00\x01\x81\x05",
                [False] * 8
                + [True]
                + [False] * 7
                + [True]
                + [False] * 6
                + [True, True, False, True],
            ),
        ],
    )
    def test_bit_packing(self, bytestream, bitlist):
        """Test all string <=> bit packing functions."""
        assert pack_bitstring(bitlist, align_byte=False) == bytestream

    @pytest.mark.parametrize(
        ("bytestream", "bitlist"),
        [
            (b"\x01", [True]),
            (b"\x00\x01", [False] * 8 + [True]),
            (b"\x05", [True, False, True]),
            (b"\x01\x05", [True] + [False] * 7 + [True, False, True]),
        ],
    )
    def test_bit_packing8(self, bytestream, bitlist):
        """Test all string <=> bit packing functions."""
        assert pack_bitstring(bitlist) == bytestream

    @pytest.mark.parametrize(
        ("align_byte", "expected"),
        [
            (True, b"\x05"),
            (False, b"\x05\x00"),
        ],
    )
    def test_pack_bitstring_does_not_mutate_input(
        self,
        align_byte,
        expected,
    ):
        """Test that pack_bitstring leaves the input list unchanged."""
        bits = [True, False, True]
        original = bits.copy()

        result = pack_bitstring(bits, align_byte=align_byte)

        assert result == expected
        assert bits == original

    @pytest.mark.parametrize(
        ("bytestream", "bitlist"),
        [
            (b"\x01", [True] + [False] * 7),
            (b"\x01\x00", [True] + [False] * 15),
            (b"\x00\x01", [False] * 8 + [True] + [False] * 7),
            (b"\x00\x80", [False] * 15 + [True]),
            (b"\x01\x80", [True] + [False] * 14 + [True]),
            (b"\x00\x05", [False] * 8 + [True, False, True] + [False] * 5),
            (b"\x01\x05", [True] + [False] * 7 + [True, False, True] + [False] * 5),
            (
                b"\x81\x05",
                [True] + [False] * 6 + [True, True, False, True] + [False] * 5,
            ),
            (
                b"\x05\x81\x01\x00",
                [True, False, True]
                + [False] * 5
                + [True]
                + [False] * 6
                + [True]
                + [True]
                + [False] * 7
                + [False] * 8,
            ),
        ],
    )
    def test_bit_unpacking(self, bytestream, bitlist):
        """Test all string <=> bit packing functions."""
        assert unpack_bitstring(bytestream) == bitlist

    def test_Exception_str(self):
        """Test string conversion of Exception."""
        assert str(self.exception) != ""
