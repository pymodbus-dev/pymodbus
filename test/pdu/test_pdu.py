"""Test pdu."""

from copy import copy
from unittest import mock

import pytest

import pymodbus.pdu.register_message as reg_msg
from pymodbus.constants import CLEAR_STATISTICS, ExcCodes
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import DecodePDU, PDUexception, pack_bitstring, unpack_bitstring
from pymodbus.pdu.diag_message import PDUgetClearModbusPlus, PDUreturnQueryData


class TestPdu:
    """Test modbus PDU."""

    @pytest.mark.parametrize(
        "cases",
        ["id", "params", "wrong_addr", "wrong_count"],
    )
    async def test_init1(self, cases, paramPDU):
        """Ensure that __init__ runs correctly."""
        pdu, _api, params, _msg, params2, _msg = paramPDU
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
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")

    @pytest.mark.parametrize(
        "cases",
        ["isError", "sub_func", "store", "str"],
    )
    async def test_init(self, cases, paramPDU):
        """Ensure that __init__ runs correctly."""
        pdu, _api, params, msg, _params2, _msg = paramPDU
        match cases:
            case "isError":
                assert not pdu(0).isError()
            case "sub_func":
                x = pdu(0)
                x_fc = x.sub_function_code
                assert x_fc == x.decode_sub_function_code(0, b"\x01" + msg)
            case "store":
                x = pdu(0, **params)
                assert await x.build_response(mock.AsyncMock(), mock.AsyncMock())
            case "str":
                x_str = str(pdu(0, **params))
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
                x = pdu(0, is_request=is_request, **params)
                fc = x.function_code.to_bytes(1, "big")
                assert msg == fc + x.to_bytes()
                x = pdu(0, is_request=is_request, **params_comb)
                assert msg == fc + x.to_bytes()
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
                result_str = str(result)
                x_str = str(x)
                for entry in params:
                    assert entry in result_str
                    assert entry in x_str
            case "calc":
                x = pdu(0, is_request=is_request)
                x.from_bytes(1, msg)
                assert len(msg) + 3 == x.calculatePduSize(is_request, 0, b"\x01" + msg)
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")

    @pytest.mark.parametrize("is_request", [True, False])
    @pytest.mark.parametrize(
        "cases", ["isError", "to_bytes", "from_bytes", "build", "calc", "str"]
    )
    async def test_PDUexception(self, is_request, cases):
        """Ensure that PDUexception is correct."""
        pdu = PDUexception(2, 0x01, 0x02, is_request=is_request)
        match cases:
            case "isError":
                assert pdu.isError()
            case "to_bytes":
                assert pdu.to_bytes() == b"\x02"
            case "from_bytes":
                pdu2 = PDUexception(2, 0x01, 0x02, is_request=is_request)
                pdu2.from_bytes(0, b"\x84\x04")
                assert pdu2.function_code == 0x84
                assert pdu2.exception_code == 0x04
            case "calc":
                assert pdu.calculatePduSize(is_request, 0, b"\x81\x05") == 5
            case "build":
                if is_request:
                    x = await pdu.build_response(mock.AsyncMock(), mock.AsyncMock())
                    assert isinstance(x, PDUexception)
                    assert x.exception_code == ExcCodes.ILLEGAL_FUNCTION
            case "str":
                x_str = str(pdu)
                for x in ("PDUexception", "dev_id", "function_code", "transaction_id"):
                    assert x in x_str
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")

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
            0, address=117, registers=registers, count=3
        )
        assert len(req.registers) == 2
        assert req.registers[0] == 24930
        assert req.registers[1] == 25444

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
                x.from_bytes(1, msg)
                assert len(msg) + 3 == DecodePDU(is_request).calculateRtuFrameSize(
                    b"\x01" + msg
                )
            case _:  # pragma: no cover
                raise TypeError("Test case not handled!")

    def test_decoder_no_fc(self):
        """Test lookup for responses."""
        msg = b"\x01\x7f\x70"
        pdu = DecodePDU._lookupPduClass(msg)
        assert not pdu
        pdu = DecodePDU(True).calculateRtuFrameSize(msg)
        assert not pdu

    def test_decoder_no_sub(self):
        """Test for unknown sub code."""
        with pytest.raises(ModbusIOException):
            DecodePDU(True).decode(b"\x08\x00\xf0\xf0\x00")

    def test_decoder_exc(self):
        """Test lookup for exception response."""
        pdu = DecodePDU._lookupPduClass(b"\x01\x81\x04")
        assert pdu == PDUexception

    @pytest.mark.parametrize(("frame"), [b"", b"\x01", b"NO FRAME"])
    def test_decoder_bad_frame(self, frame):
        """Test lookup bad frames."""
        with pytest.raises(ModbusIOException):
            DecodePDU(True).decode(frame)

    @pytest.mark.parametrize(("message"), [b"\x0c", 12, [12], [12, 24]])
    def test_diag_message(self, message):
        """Test diag message."""
        PDUreturnQueryData(0, message=message)

    @pytest.mark.parametrize(("message"), [b"\x0c", 12, [12], [12, 24]])
    async def test_diag_message2(self, message):
        """Test diag message."""
        pdu = PDUgetClearModbusPlus(0, message=CLEAR_STATISTICS)
        assert await pdu.build_response(mock.AsyncMock(), mock.AsyncMock())
