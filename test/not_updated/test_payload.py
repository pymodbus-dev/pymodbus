"""Payload Utilities Test Fixture.

This fixture tests the functionality of the payload
utilities.

* PayloadBuilder
* PayloadDecoder
"""
import pytest

from pymodbus.constants import Endian
from pymodbus.exceptions import ParameterException
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class TestPayloadUtility:
    """Modbus payload utility tests."""

    little_endian_payload = (
        b"\x01\x02\x00\x03\x00\x00\x00\x04\x00\x00\x00\x00"
        b"\x00\x00\x00\xff\xfe\xff\xfd\xff\xff\xff\xfc\xff"
        b"\xff\xff\xff\xff\xff\xff\x00\x00\xa0\x3f\x00\x00"
        b"\x00\x00\x00\x00\x19\x40\x01\x00\x74\x65\x73\x74"
        b"\x11"
    )

    big_endian_payload = (
        b"\x01\x00\x02\x00\x00\x00\x03\x00\x00\x00\x00\x00"
        b"\x00\x00\x04\xff\xff\xfe\xff\xff\xff\xfd\xff\xff"
        b"\xff\xff\xff\xff\xff\xfc\x3f\xa0\x00\x00\x40\x19"
        b"\x00\x00\x00\x00\x00\x00\x00\x01\x74\x65\x73\x74"
        b"\x11"
    )

    bitstring = [True, False, False, False, True, False, False, False]

    # ----------------------------------------------------------------------- #
    # Payload Builder Tests
    # ----------------------------------------------------------------------- #

    def test_little_endian_payload_builder(self):
        """Test basic bit message encoding/decoding."""
        builder = BinaryPayloadBuilder(byteorder=Endian.LITTLE, wordorder=Endian.LITTLE)
        builder.add_8bit_uint(1)
        builder.add_16bit_uint(2)
        builder.add_32bit_uint(3)
        builder.add_64bit_uint(4)
        builder.add_8bit_int(-1)
        builder.add_16bit_int(-2)
        builder.add_32bit_int(-3)
        builder.add_64bit_int(-4)
        builder.add_32bit_float(1.25)
        builder.add_64bit_float(6.25)
        builder.add_16bit_uint(1)  # placeholder
        builder.add_string("test")
        builder.add_bits(self.bitstring)
        assert self.little_endian_payload == builder.encode()

    def test_big_endian_payload_builder(self):
        """Test basic bit message encoding/decoding."""
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG)
        builder.add_8bit_uint(1)
        builder.add_16bit_uint(2)
        builder.add_32bit_uint(3)
        builder.add_64bit_uint(4)
        builder.add_8bit_int(-1)
        builder.add_16bit_int(-2)
        builder.add_32bit_int(-3)
        builder.add_64bit_int(-4)
        builder.add_32bit_float(1.25)
        builder.add_64bit_float(6.25)
        builder.add_16bit_uint(1)  # placeholder
        builder.add_string("test")
        builder.add_bits(self.bitstring)
        assert self.big_endian_payload == builder.encode()

    def test_payload_builder_reset(self):
        """Test basic bit message encoding/decoding."""
        builder = BinaryPayloadBuilder()
        builder.add_8bit_uint(0x12)
        builder.add_8bit_uint(0x34)
        builder.add_8bit_uint(0x56)
        builder.add_8bit_uint(0x78)
        assert builder.encode() == b"\x12\x34\x56\x78"
        assert builder.build() == [b"\x12\x34", b"\x56\x78"]
        builder.reset()
        assert not builder.encode()
        assert not builder.build()

    def test_payload_builder_with_raw_payload(self):
        """Test basic bit message encoding/decoding."""
        _coils1 = [
            False,
            False,
            True,
            True,
            False,
            True,
            False,
            False,
            False,
            False,
            False,
            True,
            False,
            False,
            True,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            True,
            False,
            True,
            False,
            True,
            True,
            False,
        ]
        _coils2 = [
            False,
            False,
            False,
            True,
            False,
            False,
            True,
            False,
            False,
            False,
            True,
            True,
            False,
            True,
            False,
            False,
            False,
            True,
            False,
            True,
            False,
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
        ]

        builder = BinaryPayloadBuilder(
            [b"\x12", b"\x34", b"\x56", b"\x78"], repack=True
        )
        assert builder.encode() == b"\x12\x34\x56\x78"
        assert builder.to_registers() == [13330, 30806]
        coils = builder.to_coils()
        assert _coils1 == coils

        builder = BinaryPayloadBuilder(
            [b"\x12", b"\x34", b"\x56", b"\x78"], byteorder=Endian.BIG
        )
        assert builder.encode() == b"\x12\x34\x56\x78"
        assert builder.to_registers() == [4660, 22136]
        assert str(builder) == "\x12\x34\x56\x78"
        coils = builder.to_coils()
        assert _coils2 == coils

    # ----------------------------------------------------------------------- #
    # Payload Decoder Tests
    # ----------------------------------------------------------------------- #

    def test_little_endian_payload_decoder(self):
        """Test basic bit message encoding/decoding."""
        decoder = BinaryPayloadDecoder(
            self.little_endian_payload, byteorder=Endian.LITTLE, wordorder=Endian.LITTLE
        )
        assert decoder.decode_8bit_uint() == 1
        assert decoder.decode_16bit_uint() == 2
        assert decoder.decode_32bit_uint() == 3
        assert decoder.decode_64bit_uint() == 4
        assert decoder.decode_8bit_int() == -1
        assert decoder.decode_16bit_int() == -2
        assert decoder.decode_32bit_int() == -3
        assert decoder.decode_64bit_int() == -4
        assert decoder.decode_32bit_float() == 1.25
        assert decoder.decode_64bit_float() == 6.25
        assert not decoder.skip_bytes(2)
        assert decoder.decode_string(4).decode() == "test"
        assert self.bitstring == decoder.decode_bits()

    def test_big_endian_payload_decoder(self):
        """Test basic bit message encoding/decoding."""
        decoder = BinaryPayloadDecoder(self.big_endian_payload, byteorder=Endian.BIG)
        assert decoder.decode_8bit_uint() == 1
        assert decoder.decode_16bit_uint() == 2
        assert decoder.decode_32bit_uint() == 3
        assert decoder.decode_64bit_uint() == 4
        assert decoder.decode_8bit_int() == -1
        assert decoder.decode_16bit_int() == -2
        assert decoder.decode_32bit_int() == -3
        assert decoder.decode_64bit_int() == -4
        assert decoder.decode_32bit_float() == 1.25
        assert decoder.decode_64bit_float() == 6.25
        assert not decoder.skip_bytes(2)
        assert decoder.decode_string(4) == b"test"
        assert self.bitstring == decoder.decode_bits()

    def test_payload_decoder_reset(self):
        """Test the payload decoder reset functionality."""
        decoder = BinaryPayloadDecoder(b"\x12\x34")
        assert decoder.decode_8bit_uint() == 0x12
        assert decoder.decode_8bit_uint() == 0x34
        decoder.reset()
        assert decoder.decode_16bit_uint() == 0x3412

    def test_payload_decoder_register_factory(self):
        """Test the payload decoder reset functionality."""
        payload = [1, 2, 3, 4]
        decoder = BinaryPayloadDecoder.fromRegisters(payload, byteorder=Endian.LITTLE)
        encoded = b"\x00\x01\x00\x02\x00\x03\x00\x04"
        assert encoded == decoder.decode_string(8)

        decoder = BinaryPayloadDecoder.fromRegisters(payload, byteorder=Endian.BIG)
        encoded = b"\x00\x01\x00\x02\x00\x03\x00\x04"
        assert encoded == decoder.decode_string(8)
        with pytest.raises(ParameterException):
            BinaryPayloadDecoder.fromRegisters("abcd")

    def test_payload_decoder_coil_factory(self):
        """Test the payload decoder reset functionality."""
        payload = [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1]
        decoder = BinaryPayloadDecoder.fromCoils(payload, byteorder=Endian.LITTLE)
        encoded = b"\x88\x11"
        assert encoded == decoder.decode_string(2)

        decoder = BinaryPayloadDecoder.fromCoils(payload, byteorder=Endian.BIG)
        encoded = b"\x88\x11"
        assert encoded == decoder.decode_string(2)

        with pytest.raises(ParameterException):
            BinaryPayloadDecoder.fromCoils("abcd")
