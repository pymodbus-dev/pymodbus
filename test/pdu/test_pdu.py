"""Test pdu."""

from unittest import mock

import pytest

import pymodbus.pdu.register_message as reg_msg
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import (
    DecodePDU,
    ModbusControlBlock,
    PDUexception,
)
from pymodbus.pdu.utils import pack_bitstring, unpack_bitstring


class TestPdu:
    """Test modbus PDU."""

    @pytest.mark.parametrize(
        "cases",
        ["id", "params", "wrong_addr", "wrong_count", "isError", "sub_func", "store"],
    )
    async def test_init(self, cases, paramPDU):
        """Ensure that __init__ runs correctly."""
        pdu, _api, params, msg, params2, _msg = paramPDU
        match cases:
            case "id":
                with pytest.raises(TypeError):
                    pdu()
                assert pdu(0)
                assert pdu(1)
                assert pdu(1, is_request=False)
                assert pdu(1, is_request=True)
                with pytest.raises(ModbusIOException):
                    pdu(-1)
                with pytest.raises(ModbusIOException):
                    pdu(256)
            case "params":
                assert pdu(1, **params)
                assert pdu(1, **params2)
                assert pdu(1, **(params | params2))
                dev_id = 63
                params_comb = params | {
                    "transaction_id": 9112,
                    "address": 517,
                    "count": 68,
                }
                pdu = pdu(dev_id, **params_comb)
                assert pdu
                assert str(pdu)
                assert 0 < pdu.function_code < 0x80
                for key, value in params_comb.items():
                    assert getattr(pdu, key) == value
            case "wrong_addr":
                z_param = params | {"address": -1}
                with pytest.raises(ModbusIOException):
                    pdu(0, **z_param)
                z_param = params | {"address": 70000}
                with pytest.raises(ModbusIOException):
                    pdu(0, **z_param)
            case "wrong_count":
                z_param = params | {"count": -1}
                with pytest.raises(ModbusIOException):
                    pdu(0, **z_param)
                z_param = params | {"count": 3000}
                with pytest.raises(ModbusIOException):
                    pdu(0, **z_param)
            case "isError":
                assert not pdu(0).isError()
            case "sub_func":
                x = pdu(0)
                x_fc = x.sub_function_code
                assert x_fc == x.decode_sub_function_code(0, b"\x01" + msg)
            case "store":
                x = pdu(0, **params)
                assert await x.build_response(mock.AsyncMock(), mock.AsyncMock())
            case _:
                raise TypeError("Test case not handled!")

    @pytest.mark.parametrize("is_request", [True, False])
    @pytest.mark.parametrize("cases", ["to_bytes", "from_bytes", "calc"])
    def test_to_from_bytes(self, is_request, cases, paramPDU):
        """Ensure that __init__ runs correctly."""
        if is_request:
            pdu, _api, params, msg, params2, _msg = paramPDU
        else:
            pdu, _api, params2, _msg, params, msg = paramPDU
        params_comb = params | params2
        match cases:
            case "to_bytes":
                x = pdu(0, is_request=is_request, **params)
                assert msg == x.function_code.to_bytes(1, "big") + x.to_bytes()
                x = pdu(0, is_request=is_request, **params_comb)
                assert msg == x.function_code.to_bytes(1, "big") + x.to_bytes()
            case "from_bytes":
                result = pdu(0, is_request=is_request, **params)
                x = pdu(0, is_request=is_request)
                x.from_bytes(1, msg)
                if "bits" in params:
                    for entry in (result, x):
                        if j := len(entry.bits) % 8:
                            entry.bits += [False] * (8 - j)
                            entry.count = len(result.bits)
                for key in params:
                    assert getattr(result, key) == getattr(x, key)
                assert str(result) == str(x)
            case "calc":
                x = pdu(0, is_request=is_request)
                x.from_bytes(1, msg)
                assert len(msg) + 3 == x.calculatePduSize(is_request, 0, b"\x01" + msg)
            case _:
                raise TypeError("Test case not handled!")


class xTestPdu:
    """Test modbus PDU."""

    exception = PDUexception(1, 1, 0)

    requests = responses = []

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests)
    @pytest.mark.usefixtures("frame", "args")
    async def test_pdu_datastore(self, pdutype, args, kwargs, mock_server_context):
        """Test that all PDU types can be created."""
        control = ModbusControlBlock()
        try:
            pdu = pdutype(*args, **kwargs)
            assert await pdu.build_response(mock.AsyncMock(), mock.AsyncMock())
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

    async def test_error_methods(self):
        """Test all error methods."""
        result = self.exception.to_bytes()
        assert result == b"\x01"
        DecodePDU(True).decode(b"\x81" + result)
        assert self.exception.exception_code == 1
        self.exception.from_bytes(0, b"")

    def test_pdu_register_as_byte(self):
        """Test verify functions."""
        registers = [int.from_bytes(b"ab", "big"), int.from_bytes(b"cd", "big")]
        # NOT ALLOWED, NO conversion.
        req = reg_msg.PDUreadHoldingRegisters(address=117, registers=registers, count=3)
        assert len(req.registers) == 2
        assert req.registers[0] == 24930
        assert req.registers[1] == 25444
