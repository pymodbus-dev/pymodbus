"""Test pdu."""

from copy import copy
from typing import Any
from unittest import mock

import pytest

import pymodbus.pdu.data_message as reg_msg
from pymodbus.constants import ExcCodes
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import (
    DecodePDU,
    ModbusPdu,
    PDUexception,
    pack_bitstring,
    unpack_bitstring,
)
from pymodbus.pdu.data_message import PDUreadCoils
from pymodbus.pdu.diag_message import PDUreadDeviceInformation


class TestPdu_alone:
    """Test modbus PDU."""

    @pytest.mark.parametrize(
        "is_request",
        [True, False],
    )
    @pytest.mark.parametrize(
        ("dev_id", "tid", "result"),
        [
            (0, 0, True),
            (-1, 0, False),
            (0, -1, False),
            (300, 0, False),
            (0, 66000, False),
        ],
    )
    def test_pdu_init(self, is_request, dev_id, tid, result):
        """Test ModbusPdu init."""
        if result:
            ModbusPdu(is_request, dev_id, tid)
        else:
            with pytest.raises(ModbusIOException):
                ModbusPdu(is_request, dev_id, tid)

    async def test_pdu_methods(self):
        """Test ModbusPdu methods."""
        pdu = ModbusPdu(True, 1, 117)
        assert not pdu.isError()
        x_str = str(pdu)
        for x in (
            ModbusPdu.__name__,
            "dev_id=1,",
            "function_code=-1,",
            "transaction_id=117",
        ):
            assert x in x_str
        assert pdu.decode_sub_function_code(b"") == -1
        assert pdu.calculatePduSize(b"") == 2
        pdu.function_code = 7
        assert pdu.preamble() == b"\x01\x07"
        pdu.from_bytes(b"\x09\x05")
        assert pdu.dev_id == 9
        assert pdu.function_code == 5  # type: ignore[comparison-overlap]
        x = await pdu.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(x, PDUexception)
        assert x.dev_id == 9
        assert x.function_code == 5 | 0x80
        assert x.exception_code == ExcCodes.DEVICE_BUSY

    async def test_PDUexception(self):
        """Ensure that PDUexception is correct."""
        pdu = PDUexception(2, 0x01, 0x02)
        assert pdu.dev_id == 2
        assert pdu.function_code == 0x81
        assert pdu.exception_code == 0x02
        assert pdu.isError()
        assert pdu.to_bytes() == b"\x02\x81\x02"
        assert not pdu.from_bytes(b"\x03\x84\x04")
        assert pdu.dev_id == 2
        assert pdu.function_code == 0x84
        assert pdu.exception_code == 0x04
        assert pdu.calculatePduSize(b"\x01\x81\x05") == 3
        x = await pdu.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(x, PDUexception)
        assert x.exception_code == ExcCodes.ILLEGAL_FUNCTION
        x_str = str(pdu)
        for x in ("PDUexception", "dev_id", "function_code", "transaction_id"):
            assert x in x_str

    @pytest.mark.parametrize("is_request", [True, False])
    def test_decoder(self, is_request):
        """Test decoder."""
        assert is_request == DecodePDU(is_request).is_server

    @pytest.mark.parametrize(
        ("msg", "result"),
        [
            (b"\x09\x82\x01", PDUexception),
            (b"\x09\x01\x03", PDUreadCoils),
            (b"\x01\x2b\x0e\x01\x02", PDUreadDeviceInformation),
            (b"\x09\x79\x01", None),
            (b"\x09\x79", None),
            (b"\x08\x00\xf0\xf0\x00", None),
        ],
    )
    def test_decoder_lookup(self, msg, result):
        """Test decoder."""
        if result:
            assert DecodePDU._lookupPduClass(msg) == result
        else:
            assert not DecodePDU._lookupPduClass(msg)

    @pytest.mark.parametrize("is_request", [True, False])
    def test_decoder_methods(self, is_request):
        """Test decoder."""
        kwargs: dict[str, Any]
        if is_request:
            kwargs = {"address": 117, "count": 3}
            msg = b"\x01\x01\x00\x75\x00\x03"
        else:
            kwargs = {"bits": [True, True] + [False] * 6}
            msg = b"\x01\x01\x01\x03"
        with pytest.raises(ModbusIOException):
            DecodePDU(is_request).decode(b"")
        with pytest.raises(ModbusIOException):
            DecodePDU(is_request).decode(b"\x01\x79")
        with pytest.raises(ModbusIOException):
            DecodePDU(is_request).decode(b"\x01\x01\x01")
        assert isinstance(DecodePDU(is_request).decode(msg), PDUreadCoils)

        x_msg = DecodePDU(is_request).encode(PDUreadCoils(is_request, 1, **kwargs))
        assert x_msg == msg

        assert len(msg) + 2 == DecodePDU(is_request).calculateRtuFrameSize(msg)
        assert DecodePDU(is_request).calculateRtuFrameSize(b"\x01\x79") == 0
        with pytest.raises(ModbusIOException):
            DecodePDU(is_request).calculateRtuFrameSize(b"\x01\x01\x01")

    @pytest.mark.parametrize(("frame"), [b"", b"\x01", b"NO FRAME"])
    def test_decoder_bad_frame(self, frame):
        """Test lookup bad frames."""
        with pytest.raises(ModbusIOException):
            DecodePDU(True).decode(frame)

    @pytest.mark.parametrize("pack", ["pack", "pack8", "unpack"])
    @pytest.mark.parametrize(
        ("pack_run", "bytestream", "bitlist", "padding"),
        [
            (  # 0
                1,
                b"\x01",
                [True],
                7,
            ),
            (  # 1
                1,
                b"\x05",
                [True, False, True],
                5,
            ),
            (  # 2
                2,
                b"\x01\x00",
                [True] + [False] * 15,
                0,
            ),
            (  # 3
                2,
                b"\x01\x00",
                [True],
                15,
            ),
            (  # 4
                3,
                b"\x00\x80",
                [False] * 15 + [True],
                0,
            ),
            (  # 5
                3,
                b"\x00\x01",
                [False] * 8 + [True] + [False] * 7,
                0,
            ),
            (  # 6
                3,
                b"\x01\x80",
                [True] + [False] * 14 + [True],
                0,
            ),
            (  # 7
                3,
                b"\x00\x05",
                [False] * 8 + [True, False, True] + [False] * 5,
                0,
            ),
            (  # 8
                3,
                b"\x01\x05",
                [True] + [False] * 7 + [True, False, True] + [False] * 5,
                0,
            ),
            (  # 9
                3,
                b"\x81\x05",
                [True] + [False] * 6 + [True, True, False, True] + [False] * 5,
                0,
            ),
            (  # 10
                3,
                b"\x00\x01\x81\x05",
                [False] * 8
                + [True]
                + [False] * 7
                + [True]
                + [False] * 6
                + [True, True, False, True]
                + [False] * 5,
                0,
            ),
            (  # 11
                3,
                b"\x00\x01",
                [False] * 8 + [True],
                7,
            ),
            (  # 12
                3,
                b"\x00\x05",
                [False] * 8 + [True, False, True],
                5,
            ),
            (  # 13
                3,
                b"\x01\x05",
                [True] + [False] * 7 + [True, False, True],
                5,
            ),
            (  # 14
                3,
                b"\x81\x05",
                [True] + [False] * 6 + [True, True, False, True],
                5,
            ),
            (  # 15
                3,
                b"\x00\x01\x81\x05",
                [False] * 8
                + [True]
                + [False] * 7
                + [True]
                + [False] * 6
                + [True, True, False, True],
                5,
            ),
        ],
    )
    def test_bit_packing(self, pack, bytestream, pack_run, bitlist, padding):
        """Test all string <=> bit packing functions."""
        original = copy(bitlist)
        match pack:
            case "pack":
                if pack_run in (2, 3):
                    assert pack_bitstring(bitlist, align_byte=False) == bytestream
            case "pack8":
                if pack_run in (1, 3):
                    original = copy(bitlist)
                    assert pack_bitstring(bitlist, align_byte=True) == bytestream
                    assert original == bitlist
            case "unpack":
                original_b = copy(bytestream)
                assert unpack_bitstring(bytestream) == bitlist + [False] * padding
                assert original_b == bytestream
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")
        assert original == bitlist

    def test_pdu_register_as_byte(self):
        """Test verify functions."""
        registers = [int.from_bytes(b"ab", "big"), int.from_bytes(b"cd", "big")]
        # NOT ALLOWED, NO conversion.
        req = reg_msg.PDUreadHoldingRegisters(
            False, 0, address=117, registers=registers, count=3
        )
        assert len(req.registers) == 2
        assert req.registers[0] == 24930
        assert req.registers[1] == 25444


class TestPdus:
    """Test modbus PDU."""

    @pytest.mark.parametrize(
        "cases",
        ["id", "params"],
    )
    async def test_init(self, cases, paramPDU):
        """Ensure that __init__ runs correctly."""
        pdu, _api, params, _msg, params2, _msg = paramPDU
        match cases:
            case "id":
                with pytest.raises(TypeError):
                    pdu()
                with pytest.raises(TypeError):
                    pdu(True)
                assert pdu(False, 0)
                assert pdu(True, 1)
                with pytest.raises(ModbusIOException):
                    pdu(True, -1)
                with pytest.raises(ModbusIOException):
                    pdu(True, 256)
            case "params":
                assert pdu(False, 1, **params)
                assert pdu(False, 1, **params2)
                assert pdu(False, 1, **(params | params2))
                dev_id = 63
                params_comb = params | {
                    "transaction_id": 9112,
                }
                pdu_obj = pdu(True, dev_id, **params_comb)
                assert pdu_obj
                assert str(pdu_obj)
                assert 0 < pdu.function_code < 0x80
                for key, value in params_comb.items():
                    assert getattr(pdu_obj, key) == value
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")

    @pytest.mark.parametrize(
        "cases",
        ["isError", "sub_func", "store", "str"],
    )
    async def test_methods(self, cases, paramPDU):
        """Ensure that __init__ runs correctly."""
        pdu, _api, params, msg, _params2, _msg = paramPDU
        match cases:
            case "isError":
                assert not pdu(False, 0).isError()
            case "sub_func":
                x = pdu(False, 0)
                x_fc = x.sub_function_code
                assert x_fc == x.decode_sub_function_code(msg)
            case "store":
                x = pdu(False, 0, **params)
                assert await x.build_response(mock.AsyncMock(), mock.AsyncMock())
            case "str":
                x_str = str(pdu(False, 0, **params))
                for x in (pdu.__name__, "dev_id", "function_code", "transaction_id"):
                    assert x in x_str
                for key in params:
                    assert key in x_str
            case _:  # pragma: no cover
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
                x = pdu(is_request, 1, **params)
                assert msg == x.to_bytes()
                x = pdu(is_request, 1, **params_comb)
                assert msg == x.to_bytes()
            case "from_bytes":
                result = pdu(is_request, 1, **params)
                x = pdu(is_request, 1)
                x.from_bytes(msg)
                if "bits" in params:
                    for entry in (result, x):
                        if j := len(entry.bits) % 8:
                            entry.bits += [False] * (8 - j)
                            entry.count = len(result.bits)
                for key in params:
                    assert getattr(result, key) == getattr(x, key)
                result_str = str(result)
                x_str = str(x)
                for entry in params:
                    assert entry in result_str
                    assert entry in x_str
            case "calc":
                x = pdu(is_request, 1)
                x.from_bytes(msg)
                assert len(msg) == x.calculatePduSize(msg)
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")


class XTestPdus:
    """Test modbus PDU."""

    @pytest.mark.parametrize("cases", ["lookup"])
    def test_decoder1(self, cases, paramPDU):
        """Test decoder."""
        pdu, _api, _params, msg, _params2, _msg = paramPDU
        match cases:
            case "lookup":
                result = DecodePDU._lookupPduClass(b"\x01" + msg)
                assert result == pdu
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")

    @pytest.mark.parametrize("is_request", [True, False])
    @pytest.mark.parametrize("cases", ["decode", "encode", "calc"])
    def test_decoder2(self, is_request, cases, paramPDU):
        """Test decoder."""
        if is_request:
            pdu, _api, params, msg, _params2, _msg = paramPDU
        else:
            pdu, _api, _params2, _msg, params, msg = paramPDU
        match cases:
            case "decode":
                x_pdu = DecodePDU(is_request).decode(msg)
                assert isinstance(x_pdu, pdu)
            case "encode":
                x_pdu = pdu(0, is_request=is_request, **params)
                x_msg = DecodePDU(is_request).encode(x_pdu)
                assert x_msg == msg[1:]
            case "calc":
                x = pdu(0, is_request=is_request)
                x.from_bytes(msg)
                assert len(msg) + 3 == DecodePDU(is_request).calculateRtuFrameSize(
                    b"\x01" + msg
                )
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")
